#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri May 18 10:16:49 2018

@author: chenjiwei
"""

import tensorflow as tf
import numpy as np
import train
from PIL import Image
import cv2

dz=train.Ocr()
output = dz.crack_captcha_cnn()
saver = tf.train.Saver()

def captcha_text_and_image(filename):
    fn=filename.split('.')[0]
    captcha_text=fn.split('/')[-1]
    captcha_image = Image.open(filename)
    captcha_image = np.array(captcha_image)
    return captcha_text, captcha_image


    
def crack_captcha(captcha_image):
    with tf.Session() as sess:
        saver.restore(sess, tf.train.latest_checkpoint("./model"))
        predict = tf.argmax(tf.reshape(output, [-1, dz.max_captcha, dz.char_set_len]), 2)
        text_list = sess.run(predict, feed_dict={dz.X: [captcha_image], dz.keep_prob: 1})
        text = text_list[0].tolist()
        vector = np.zeros(dz.max_captcha*dz.char_set_len)
        i = 0
        for n in text:
                vector[i*dz.char_set_len + n] = 1
                i += 1
        return dz.vec2text(vector)


if __name__ == '__main__':
    filename='./1521636710.png'
    text, image =captcha_text_and_image(filename)
    image = np.mean(cv2.imread(filename),-1)
    image = image.flatten() / 255
    predict_text = crack_captcha(image)
    print("正确: {} 预测: {}".format(text, predict_text))
