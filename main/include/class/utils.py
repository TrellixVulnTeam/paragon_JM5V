#!/usr/bin/python
# ==============================================================================
# Copyright 2018 The Paragon Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================



import cv2
import numpy as np
from scipy import ndimage
import os
import errno
import sys
import logging
import shutil



def read_images_from_single_face_profile(face_profile, face_profile_name_index, dim = (50, 50)):

    X_data = np.array([])
    index = 0
    for the_file in os.listdir(face_profile):
        file_path = os.path.join(face_profile, the_file)
        if file_path.endswith(".png") or file_path.endswith(".jpg") or file_path.endswith(".jpeg") or file_path.endswith(".pgm"):
            img = cv2.imread(file_path, 0)
            img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
            img_data = img.ravel()
            X_data = img_data if not X_data.shape[0] else np.vstack((X_data,img_data))
            index += 1

    if index == 0 :
        shutil.rmtree(face_profile)
        logging.error("\nThere exists face profiles without images")

    Y_data = np.empty(index, dtype = int)
    Y_data.fill(face_profile_name_index)
    return X_data, Y_data

def delete_empty_profile(face_profile_directory):

    for face_profile in os.listdir(face_profile_directory):
        if "." not in str(face_profile):
            face_profile = os.path.join(face_profile_directory, face_profile)
            index = 0
            for the_file in os.listdir(face_profile):
                file_path = os.path.join(face_profile, the_file)
                if file_path.endswith(".png") or file_path.endswith(".jpg") or file_path.endswith(".jpeg") or file_path.endswith(".pgm"):
                    index += 1
            if index == 0 :
                shutil.rmtree(face_profile)
                print ("\nDeleted ", face_profile, " because it contains no images")
            if index < 2 :
                logging.error("\nFace profile " + str(face_profile) + " contains too little images (At least 2 images are needed)")


def load_training_data(face_profile_directory):

    delete_empty_profile(face_profile_directory)  # delete profile directory without images

    # Get a the list of folder names in face_profile as the profile names
    face_profile_names = [d for d in os.listdir(face_profile_directory) if "." not in str(d)]

    if len(face_profile_names) < 2:
        logging.error("\nFace profile contains too little profiles (At least 2 profiles are needed)")
        exit()

    first_data = str(face_profile_names[0])
    first_data_path = os.path.join(face_profile_directory, first_data)
    X1, y1 = read_images_from_single_face_profile(first_data_path, 0)
    X_data = X1
    Y_data = y1
    print ("Loading Database: ")
    print (0, "    ",X1.shape[0]," images are loaded from:", first_data_path)
    for i in range(1, len(face_profile_names)):
        directory_name = str(face_profile_names[i])
        directory_path = os.path.join(face_profile_directory, directory_name)
        tempX, tempY = read_images_from_single_face_profile(directory_path, i)
        X_data = np.concatenate((X_data, tempX), axis=0)
        Y_data = np.append(Y_data, tempY)
        print (i, "    ",tempX.shape[0]," images are loaded from:", directory_path)

    return X_data, Y_data, face_profile_names


def rotate_image(img, rotation, scale = 1.0):

    if rotation == 0: return img
    h, w = img.shape[:2]
    rot_mat = cv2.getRotationMatrix2D((w/2, h/2), rotation, scale)
    rot_img = cv2.warpAffine(img, rot_mat, (w, h), flags=cv2.INTER_LINEAR)
    return rot_img

def trim(img, dim):

    # if the img has a smaller dimension then return the origin image
    if dim[1] >= img.shape[0] and dim[0] >= img.shape[1]: return img
    x = int((img.shape[0] - dim[1])/2) + 1
    y = int((img.shape[1] - dim[0])/2) + 1
    trimmed_img = img[x: x + dim[1], y: y + dim[0]]   # crop the image
    return trimmed_img



def clean_directory(face_profile):

    for the_file in os.listdir(face_profile):
        file_path = os.path.join(face_profile, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print (e)


def create_directory(face_profile):

    try:
        print ("Making directory")
        os.makedirs(face_profile)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            print ("The specified face profile already existed, it will be override")
            raise

def create_profile_in_database(face_profile_name, database_path="../face_profiles/", clean_directory=False):

    face_profile_path = database_path + face_profile_name + "/"
    create_directory(face_profile_path)
    # Delete all the pictures before recording new
    if clean_directory:
        clean_directory(face_profile_path)
    return face_profile_path



