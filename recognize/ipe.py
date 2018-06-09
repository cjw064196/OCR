#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri May 18 10:16:49 2018

@author: chenjiwei
"""

import tensorflow as tf
import numpy as np
from PIL import Image
import cv2
import os

class Ocr():
    def __init__(self):
    		
        self.width = 24
        self.heigth = 64
        self.X = tf.placeholder(tf.float32, [None, 24*64])
    		# 输入数据Y占位符
        self.Y = tf.placeholder(tf.float32, [None, 63*4])
        self.char_set_len = 63
    		# keepout占位符
        self.keep_prob = tf.placeholder(tf.float32)
            
    def text2vec(self, text):
        vector = np.zeros(4 * 63)
        def char2pos(c):
            if c =='_':
                k = 62
                return k
            k = ord(c) - 48
            if k > 9:
                k = ord(c) - 55
                if k > 35:
                    k = ord(c) - 61
                    if k > 61:
                        raise ValueError('No Map') 
            return k
        for i, c in enumerate(text):
            idx = i * 63+ char2pos(c)
            vector[idx] = 1
        return vector
 
    def vec2text(self, vec):
        char_pos = vec.nonzero()[0]
        text = []
        for i, c in enumerate(char_pos):
            char_at_pos = i #c/63
            char_idx = c % self.char_set_len
            if char_idx < 10:
                char_code = char_idx + ord('0')
            elif char_idx < 36:
                char_code = char_idx - 10 + ord('A')
            elif char_idx < 62:
                char_code = char_idx - 36 + ord('a')
            elif char_idx == 62:
                char_code = ord('_')
            else:
                raise ValueError('error')
            text.append(chr(char_code))
        return "".join(text)

    def crack_captcha_cnn(self, w_alpha=0.01, b_alpha=0.1):
            
        x = tf.reshape(self.X, shape=[-1, self.heigth, self.width, 1])
		
        w_c1 = tf.Variable(w_alpha*tf.random_normal([3, 3, 1, 32]))
  
        b_c1 = tf.Variable(b_alpha*tf.random_normal([32]))	
		
        conv1 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(x, w_c1, strides=[1, 1, 1, 1], padding='SAME'), b_c1))
		
        conv1 = tf.nn.max_pool(conv1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
	
        w_c2 = tf.Variable(w_alpha*tf.random_normal([3, 3, 32, 64]))
        b_c2 = tf.Variable(b_alpha*tf.random_normal([64]))
		
        conv2 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv1, w_c2, strides=[1, 1, 1, 1], padding='SAME'), b_c2))
	
        conv2 = tf.nn.max_pool(conv2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')

        w_c3 = tf.Variable(w_alpha*tf.random_normal([3, 3, 64, 64]))
        b_c3 = tf.Variable(b_alpha*tf.random_normal([64]))
   
        conv3 = tf.nn.relu(tf.nn.bias_add(tf.nn.conv2d(conv2, w_c3, strides=[1, 1, 1, 1], padding='SAME'), b_c3))
	
        conv3 = tf.nn.max_pool(conv3, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
  
        w_d = tf.Variable(w_alpha*tf.random_normal([3*8*64, 1024]))
        b_d = tf.Variable(b_alpha*tf.random_normal([1024]))

        dense = tf.reshape(conv3, [-1, w_d.get_shape().as_list()[0]])

        dense = tf.nn.relu(tf.add(tf.matmul(dense, w_d), b_d))
        dense = tf.nn.dropout(dense, self.keep_prob)

        w_out = tf.Variable(w_alpha*tf.random_normal([1024, 4*63]))
 
        b_out = tf.Variable(b_alpha*tf.random_normal([4*63]))
		
        out = tf.add(tf.matmul(dense, w_out), b_out)
	
        return out


dz=Ocr()
output = dz.crack_captcha_cnn()
saver = tf.train.Saver()

def captcha_text_and_image(filename):
    fn=filename.split('.')[0]
    captcha_text=fn.split('/')[-1]
    # captcha_image = Image.open(filename)
    # captcha_image = np.array(captcha_image)
    captcha_image = np.mean(cv2.imread(filename),-1)
    captcha_image = captcha_image.flatten() / 255
    return captcha_text, captcha_image


    
def crack_captcha(captcha_image):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with tf.Session() as sess:
        saver.restore(sess, tf.train.latest_checkpoint(dir_path + "/ipe/model"))
        predict = tf.argmax(tf.reshape(output, [-1, 4, 63]), 2)
        text_list = sess.run(predict, feed_dict={dz.X: [captcha_image], dz.keep_prob: 1})
        text = text_list[0].tolist()
        vector = np.zeros(4*63)
        i = 0
        for n in text:
                vector[i*63 + n] = 1
                i += 1
        return dz.vec2text(vector)


if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    filename = dir_path + '/ipe/1.png'
    text, image =captcha_text_and_image(filename)
    image = np.mean(cv2.imread(filename),-1)
    image = image.flatten() / 255
    predict_text = crack_captcha(image)
    print("正确: {} 预测: {}".format(text, predict_text))
