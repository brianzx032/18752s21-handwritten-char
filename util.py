'''
Reference: 16720 Computer Vision S21 HW1
'''
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing


def get_num_CPU():
    '''
    Counts the number of CPUs available in the machine.
    '''
    return multiprocessing.cpu_count()


def display_hog_images(hog_images):
    '''
    Visualizes the hog.
    '''

    n_scale = 3
    plt.figure(1)
    hog_images = hog_images.reshape((-1, 64, 64, 3))

    for i in range(5):
        for j in range(n_scale):
            plt.subplot(5, n_scale, i*n_scale + j+1)
            hog = hog_images[i, :, :, j]
            hog_min = hog.min(axis=(0, 1), keepdims=True)
            hog_max = hog.max(axis=(0, 1), keepdims=True)
            hog = (hog - hog_min) / (hog_max - hog_min)
            plt.imshow(hog)
            plt.axis("off")

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95,
                        bottom=0.05, wspace=0.05, hspace=0.05)
    plt.show()


def display_filter_responses(opts, response_maps):
    '''
    Visualizes the filter response maps.
    '''

    n_scale = len(opts.filter_scales)
    plt.figure(1)

    for i in range(n_scale * 5):
        plt.subplot(n_scale, 5, i + 1)
        resp = response_maps[:, :, i * 3:i * 3 + 3]
        resp_min = resp.min(axis=(0, 1), keepdims=True)
        resp_max = resp.max(axis=(0, 1), keepdims=True)
        resp = (resp - resp_min) / (resp_max - resp_min)
        plt.imshow(resp)
        plt.axis("off")

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95,
                        bottom=0.05, wspace=0.05, hspace=0.05)
    plt.show()


def visualize_wordmap(original_image, wordmap, out_path=None):
    '''
    Visualizes the wordmap corresponding to an image.
    '''
    fig = plt.figure(2, figsize=(12.8, 4.8))
    ax = fig.add_subplot(1, 2, 1)
    ax.imshow(original_image)
    plt.axis("off")
    ax = fig.add_subplot(1, 2, 2)
    ax.imshow(wordmap)
    plt.axis("off")
    plt.show()
    if out_path:
        plt.savefig(out_path, pad_inches=0)
