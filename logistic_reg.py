from os.path import join
from time import time_ns

import matplotlib.pyplot as plt
import numpy as np
import scipy.io
import skimage.color
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from PIL import Image
from skimage.transform import resize
from torch.utils.data import DataLoader, TensorDataset
from opts import get_opts
import string
import util
import bag_of_words
opts = get_opts()


def train_model(model, trainset, validset, param):
    batch_size, learning_rate, epoch_num, weight_decay, alpha, pattern_sz, threshold = param

    def run_epoch(dataloader, batch_num, no_grad):
        total_loss = 0.0
        total_acc = 0.0
        for x, y in dataloader:
            x, y = x.to(device), y.to(device)
            y_pred = model(x)
            loss = criterion(y_pred, y)
            if not no_grad:
                loss.backward()
                optimizer.step()
                optimizer.zero_grad()
            total_loss += loss.item()
            pred = torch.argmax(sm(y_pred), dim=1)
            acc = torch.sum(pred == y)/x.shape[0]
            total_acc += acc/batch_num
        return total_acc, total_loss
    # get device
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    param_str = model.feat_name + \
        '_lr{:.1}w{:.1}a{}ps{}thrs{:.2}'.format(
            learning_rate, weight_decay, alpha, pattern_sz, threshold)
    print(param_str, ':', device)

    # dataloader
    trainloader = DataLoader(trainset,
                             batch_size=batch_size,
                             shuffle=True)
    validloader = DataLoader(validset,
                             batch_size=batch_size,
                             shuffle=False)
    # batch num
    train_batch_num = np.ceil(len(trainset)/batch_size)
    valid_batch_num = np.ceil(len(validset)/batch_size)

    optimizer = optim.Adam(
        model.parameters(), lr=learning_rate, weight_decay=weight_decay)

    criterion = nn.CrossEntropyLoss()
    sm = nn.Softmax(dim=1)

    # run on gpu
    criterion.to(device)
    model.to(device)
    sm.to(device)

    list_of_train_acc_per_iter = []
    list_of_valid_acc_per_iter = []
    list_of_train_loss_per_iter = []
    list_of_valid_loss_per_iter = []

    start_time = time_ns()
    for epoch in range(epoch_num):
        train_acc, running_loss = run_epoch(
            trainloader, train_batch_num, False)
        with torch.no_grad():
            valid_acc, valid_loss = run_epoch(
                validloader, valid_batch_num, True)
        list_of_train_acc_per_iter.append(train_acc)
        list_of_valid_acc_per_iter.append(valid_acc)
        list_of_train_loss_per_iter.append(running_loss)
        list_of_valid_loss_per_iter.append(valid_loss)
        if epoch % 20 == 19:
            Avg_time = (time_ns() - start_time)//20
            Avg_second = Avg_time/1e9
            print('[%d] loss: %.3f acc: %.3f valid_loss: %.3f valid_acc: %.3f Avg_time: %d\'%d\'\'%dms' %
                  (epoch + 1, running_loss, train_acc, valid_loss, valid_acc,
                   Avg_second//60, Avg_second % 60, (Avg_time // 1e6) % 1e3))
            start_time = time_ns()

    print('Finished Training')

    PATH = join(opts.out_dir, param_str+'.pth')
    torch.save(model.state_dict(), PATH)

    fig, (ax1, ax2) = plt.subplots(1, 2)
    ax1.plot(list_of_train_acc_per_iter, 'b')
    ax1.plot(list_of_valid_acc_per_iter, 'r')
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Accuracy')
    ax1.legend(['train', 'valid'])

    ax2.plot(list_of_train_loss_per_iter, 'b')
    ax2.plot(list_of_valid_loss_per_iter, 'r')
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Loss')
    ax2.legend(['train', 'valid'])
    plt.savefig(join(opts.out_dir, param_str+'.png'))
    # plt.show()
    plt.close()
    return valid_acc


def test_model(model, testset, param):
    batch_size, learning_rate, epoch_num, weight_decay, alpha, pattern_sz, threshold = param
    # get device
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    param_str = model.feat_name + \
        '_lr{:.1}w{:.1}a{}ps{}thrs{:.2}'.format(
            learning_rate, weight_decay, alpha, pattern_sz, threshold)
    print(param_str, ':', device)

    # dataloader
    testloader = DataLoader(testset, batch_size=batch_size, shuffle=False)

    # batch num
    batch_num = np.ceil(len(testset)/batch_size)

    sm = nn.Softmax(dim=1)

    # run on gpu
    model.to(device)
    sm.to(device)

    confusion = np.zeros((36, 36))
    with torch.no_grad():
        for x, y in testloader:
            x, y = x.to(device), y.to(device)
            y_pred = torch.argmax(sm(model(x)), dim=1)
            for t, p in zip(y, y_pred):
                confusion[t, p] += 1

    # plt.show()
    return confusion


''' models '''


class LR(nn.Module):
    def __init__(self, feat_name, D_in, D_out):
        super().__init__()
        self.fc1 = nn.Linear(D_in, D_out)
        self.D_in = D_in
        self.feat_name = feat_name

    def forward(self, x):
        x = x.view(-1, self.D_in)
        x = self.fc1(x)
        return x

# npz_data = np.load(join(opts.feat_dir, 'zm.npz'))
# logreg = LR('logistic-regression', 25, 36)

# npz_data = np.load(join(opts.feat_dir, 'hog.npz'))
# logreg = LR('logistic-regression', 64*64*3, 36)


best_param = [0 for i in range(7)]
best_val_acc = 0
for alpha in range(5, 15, 3):
    opts.alpha = alpha
    for threshold in np.arange(0.05, 0.2, 0.03):
        opts.thres = threshold
        for pattern_size in range(7, 13, 1):
            opts.pattern_size = pattern_size

            bag_of_words.main(["extract"], opts)

            npz_data = np.load(join(opts.feat_dir, 'bow_feature.npz'))
            logreg = LR("hog_corner", opts.pattern_size *
                        opts.pattern_size*opts.alpha, 36)
            dataset = TensorDataset(torch.from_numpy(npz_data["features"].astype(np.float32)),
                                    torch.from_numpy(npz_data["labels"]))
            valid_num = len(dataset)//5
            test_num = valid_num
            train_num = len(dataset)-valid_num-valid_num
            trainset, validset, testset = torch.utils.data.random_split(
                dataset, [train_num, valid_num, test_num])

            for lr in np.arange(1e-3, 1.5e-3, 2e-4):
                for w in np.arange(1e-3, 1.5e-3, 2e-4):
                    valid_acc = train_model(logreg, trainset, validset, [
                                            opts.batch_size, lr, opts.epoch, w, alpha, pattern_size, threshold])
                    if valid_acc > best_val_acc:
                        best_param = [opts.batch_size, lr, opts.epoch,
                                      w, alpha, pattern_size, threshold]
                        best_val_acc = valid_acc
print(best_param)
confusion = test_model(logreg, testset, best_param)
accuracy = np.sum(confusion.diagonal()) / np.sum(confusion)
print(accuracy)
util.visualize_confusion_matrix(confusion)
