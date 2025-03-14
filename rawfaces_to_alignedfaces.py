#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
###################################################################
# File Name: raw_faces_to_aligned_faces.py
# Author: Abhik Sarkar
# mail: abhiksark@gmail.com
# Created Time: Thu Oct  5 02:27:35 2017 IST
###################################################################
"""


from __future__ import absolute_import, division, print_function

import argparse
import os
import random
import sys
from time import sleep

import numpy as np
import tensorflow as tf
from scipy import misc

import face_recognition.detect_face as detect_face
import face_recognition.facenet as facenet

OUTPUT_DIR = './faces'
DATA_DIR = './raw_faces'

output_dir = os.path.expanduser(OUTPUT_DIR)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

dataset = facenet.get_dataset(DATA_DIR)

print('Creating networks and loading parameters')
with tf.Graph().as_default():
    #gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
    sess = tf.Session()
    with sess.as_default():
        pnet, rnet, onet = detect_face.create_mtcnn(sess, './data')

minsize = 40  # minimum size of face
threshold = [0.6, 0.7, 0.7]  # three steps's threshold
factor = 0.709  # scale factor 0.709
margin = 44
image_size = 182

# Add a random key to the filename to allow alignment using multiple processes
random_key = np.random.randint(0, high=99999)
bounding_boxes_filename = os.path.join(
    output_dir, 'bounding_boxes_%05d.txt' % random_key)
print('Goodluck')

with open(bounding_boxes_filename, "w") as text_file:
    nrof_images_total = 0
    nrof_successfully_aligned = 0
    for cls in dataset:
        output_class_dir = os.path.join(output_dir, cls.name)
        if not os.path.exists(output_class_dir):
            os.makedirs(output_class_dir)
        for image_path in cls.image_paths:
            nrof_images_total += 1
            filename = os.path.splitext(os.path.split(image_path)[1])[0]
            output_filename = os.path.join(output_class_dir, f'{filename}.jpg')
            print(image_path)
            if not os.path.exists(output_filename):
                try:
                    img = misc.imread(image_path)
                    print('read data dimension: ', img.ndim)
                except (IOError, ValueError, IndexError) as e:
                    errorMessage = f'{image_path}: {e}'
                    print(errorMessage)
                else:
                    if img.ndim < 2:
                        print('Unable to align "%s"' % image_path)
                        text_file.write('%s\n' % (output_filename))
                        continue
                    if img.ndim == 2:
                        img = facenet.to_rgb(img)
                        print('to_rgb data dimension: ', img.ndim)
                    img = img[:, :, 0:3]
                    print('after data dimension: ', img.ndim)

                    bounding_boxes, _ = detect_face.detect_face(
                        img, minsize, pnet, rnet, onet, threshold, factor)
                    nrof_faces = bounding_boxes.shape[0]
                    print('detected_face: %d' % nrof_faces)
                    print("")
                    print(_)
                    print("")
                    print(bounding_boxes.shape)
                    counter = nrof_faces
                    det = bounding_boxes[:, 0:4]
                    img_size = np.asarray(img.shape)[:2]

                    if counter == 1:
                        det = np.squeeze(det)
                        bb_temp = np.zeros(4, dtype=np.int32)
                        bb_temp[0] = det[0]
                        bb_temp[1] = det[1]
                        bb_temp[2] = det[2]
                        bb_temp[3] = det[3]
                        try:
                            cropped_temp = img[bb_temp[1]:bb_temp[3], bb_temp[0]:bb_temp[2], :]
                            scaled_temp = misc.imresize(
                                cropped_temp, (image_size, image_size), interp='bilinear')
                        except (ValueError) as e:
                            print("No Print")
                            continue
                        nrof_successfully_aligned += 1
                        misc.imsave(output_filename, scaled_temp)
                        text_file.write('%s %d %d %d %d\n' % (
                            output_filename, bb_temp[0], bb_temp[1], bb_temp[2], bb_temp[3]))

                    if counter > 1:
                        bounding_box_size = (
                            det[:, 2] - det[:, 0]) * (det[:, 3] - det[:, 1])
                        img_center = img_size / 2
                        offsets = np.vstack([(det[:, 0] + det[:, 2]) / 2 - img_center[1],
                                             (det[:, 1] + det[:, 3]) / 2 - img_center[0]])
                        offset_dist_squared = np.sum(np.power(offsets, 2.0), 0)
                        # some extra weight on the centering
                        index = np.argmax(
                            bounding_box_size - offset_dist_squared * 2.0)
                        #det = det[index, :]
                        det_morethanone = det
                        for i in range(counter):
                            det = det_morethanone[int(i), :]
                            det = np.squeeze(det)
                            bb_temp = np.zeros(4, dtype=np.int32)
                            bb_temp[0] = det[0]
                            bb_temp[1] = det[1]
                            bb_temp[2] = det[2]
                            bb_temp[3] = det[3]
                            try:
                                cropped_temp = img[bb_temp[1]:bb_temp[3], bb_temp[0]:bb_temp[2], :]
                                scaled_temp = misc.imresize(
                                    cropped_temp, (image_size, image_size), interp='bilinear')
                            except (ValueError) as e:
                                print("No Print")
                                continue
                            nrof_successfully_aligned += 1
                            misc.imsave(
                                output_filename[:-4]+str(i)+"1.jpg", scaled_temp)
                            text_file.write('%s %d %d %d %d\n' % (
                                output_filename, bb_temp[0], bb_temp[1], bb_temp[2], bb_temp[3]))
                    else:
                        print('Unable to align "%s"' % image_path)
                        text_file.write('%s\n' % (output_filename))

print('Total number of images: %d' % nrof_images_total)
print('Number of successfully aligned images: %d' % nrof_successfully_aligned)
