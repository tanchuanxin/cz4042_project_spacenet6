import numpy as np
import os
import random
import tensorflow as tf
# import .helper as helper
# from matplotlib import pyplot as plt

# Set seed for repeatable results
seed = 40
np.random.seed(seed)
tf.random.set_seed(seed)

#np arrays must be rebuilt
def rot90(image,mask):
    k = random.randint(1,3)
    new_img = tf.image.rot90(image,k)
    new_mask = tf.image.rot90(mask,k)
    return new_img,new_mask

#np arrays must be rebuilt
def flip_lr(image,mask):
    new_image = tf.image.flip_left_right(image)
    new_mask = tf.image.flip_left_right(mask)
    return new_image,new_mask

def flip_ud(image,mask):
    new_image = tf.image.flip_up_down(image)
    new_mask = tf.image.flip_up_down(mask)
    return new_image, new_mask

#blend 2 images together
def blend(img1,img2):
    alpha = 0.7 + random.random() * 0.4
    uint8_cast = tf.cast(img1*alpha + (1-alpha)*img2, dtype=tf.uint8)
    return tf.cast(uint8_cast, tf.float32)

#grayscale image only
def grayscale(image):
    alpha = tf.reshape(tf.constant([0.25,0.25,0.25]), (1,1,3))
    return tf.math.reduce_sum(alpha*image,axis=2,keepdims=True)

def saturation(image):
    gs = grayscale(image)
    return blend(image,gs)

def brightness(image):
    gs = tf.zeros_like(image)
    return blend(image,gs)

def contrast(image):
    gs = grayscale(image)
    gs = tf.repeat(gs.mean(), 3)
    return blend(image,gs)

def gauss_noise(image):
    image = image.numpy()
    gauss = np.random.normal(10,10.0**0.5,image.shape).astype(np.uint8)
    new_image = np.copy(image)
    new_image+=gauss-np.min(gauss)
    return tf.convert_to_tensor(new_image, dtype=tf.float32)

def gamma(image):
    image = image.numpy()
    gamma = 0.7+0.4*random.random()
    new_image = np.copy(image)
    new_image = np.clip(new_image,a_min=0.0,a_max=None)
    new_image = np.power(new_image,gamma).astype(np.uint8)
    return tf.convert_to_tensor(new_image, dtype=tf.float32)

#Prob variables needed: rot90_prob,flipud_prob,fliplr_prob,color_aug(for brightness,
#contrast,saturation), gauss_prob, gamma_prob
def data_augment(image,mask,rot90_prob=0.4,flipud_prob=0.3,fliplr_prob=0.5,color_aug_prob=0.3,gauss_aug_prob=0.4,gamma_prob=0.2):
    print(image.shape)
    print(mask.shape)

    if random.random() < rot90_prob:
        image,mask = rot90(image,mask)
    if random.random() < fliplr_prob:
        image,mask = flip_lr(image,mask)
    if random.random() < flipud_prob:
        image,mask = flip_ud(image,mask)
    if random.random() < color_aug_prob:
        image = saturation(image)
    if random.random() < color_aug_prob:
        image = brightness(image)
    if random.random() < color_aug_prob:
        image = contrast(image)
    if random.random() < gauss_aug_prob:
        image = gauss_noise(image)
    if random.random() < gamma_prob:
        image = gamma(image)

    return image,mask