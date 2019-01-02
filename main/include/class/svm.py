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
import os
import numpy as np
from scipy import ndimage
from time import time
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from sklearn.cross_validation import train_test_split

from sklearn.datasets import fetch_lfw_people
from sklearn.grid_search import GridSearchCV
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.decomposition import RandomizedPCA
from sklearn.svm import SVC

import utils as ut


def test_SVM(face_profile_data, face_profile_name_index, face_dim, face_profile_names):

    X = face_profile_data
    y = face_profile_name_index

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    # Compute a PCA (eigenfaces) on the face dataset (treated as unlabeled
    # dataset): unsupervised feature extraction / dimensionality reduction
    n_components = 150 # maximum number of components to keep

    print("\nExtracting the top %d eigenfaces from %d faces" % (n_components, X_train.shape[0]))

    pca = RandomizedPCA(n_components=n_components, whiten=True).fit(X_train)
    eigenfaces = pca.components_.reshape((n_components, face_dim[0], face_dim[1]))

    # This portion of the code is used if the data is scarce, it uses the number
    # of imputs as the number of features
    # pca = RandomizedPCA(n_components=None, whiten=True).fit(X_train)
    # eigenfaces = pca.components_.reshape((pca.components_.shape[0], face_dim[0], face_dim[1]))

    print("\nProjecting the input data on the eigenfaces orthonormal basis")
    X_train_pca = pca.transform(X_train)
    X_test_pca = pca.transform(X_test)

    # Train a SVM classification model

    print("\nFitting the classifier to the training set")
    param_grid = {'C': [1e3, 5e3, 1e4, 5e4, 1e5],
                  'gamma': [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.1], }
    # clf = GridSearchCV(SVC(kernel='rbf', class_weight='balanced'), param_grid)
    # Train_pca Test Error Rate:  0.0670016750419
    # Train_pca Test Recognition Rate:  0.932998324958



    # clf = SVC(kernel='linear', C=1)
    # 2452  samples from  38  people are loaded
    # Extracting the top 150 eigenfaces from 1839 faces
    # Extracting the top 150 eigenfaces from 1790 faces
    # Train_pca Test Error Rate:  0.0904522613065
    # Train_pca Test Recognition Rate:  0.909547738693

    # clf = SVC(kernel='poly')
    # Train_pca Test Error Rate:  0.201005025126
    # Train_pca Test Recognition Rate:  0.798994974874

    # clf = SVC(kernel='sigmoid')
    # Train_pca Test Error Rate:  0.985318107667
    # Train_pca Test Recognition Rate:  0.0146818923328


    # clf = SVC(kernel='rbf').fit(X_train, y_train)
    # Train_pca Test Error Rate:  0.0619765494137
    # Train_pca Test Recognition Rate:  0.938023450586



    # Best Estimator found using Radial Basis Function Kernal:
    clf = SVC(C=1000.0, cache_size=200, class_weight='balanced', coef0=0.0,
  decision_function_shape=None, degree=3, gamma=0.0001, kernel='rbf',
  max_iter=-1, probability=False, random_state=None, shrinking=True,
  tol=0.001, verbose=False)
    # Train_pca with Alex Test Error Rate:  0.088424437299
    # Train_pca with Alex Test Recognition Rate:  0.911575562701

    clf = clf.fit(X_train_pca, y_train)
    # print("\nBest estimator found by grid search:")
    # print(clf.best_estimator_)

    ###############################################################################
    # Quantitative evaluation of the model quality on the test set
    print("\nPredicting people's names on the test set")
    t0 = time()
    y_pred = clf.predict(X_test_pca)
    print("\nPrediction took %0.8f second per sample on average" % ((time() - t0)/y_pred.shape[0]*1.0))

    # print "predicated names: ", y_pred
    # print "actual names: ", y_test
    error_rate = errorRate(y_pred, y_test)
    print ("\nTest Error Rate: %0.4f %%" % (error_rate * 100))
    print ("Test Recognition Rate: %0.4f %%" % ((1.0 - error_rate) * 100))

    ###############################################################################
    # Testing

    # X_test_pic1 = X_test[0]
    # X_test_pic1_for_display = np.reshape(X_test_pic1, face_dim)

    # t0 = time()
    # pic1_pred_name = predict(clf, pca, X_test_pic1, face_profile_names)
    # print("\nPrediction took %0.3fs" % (time() - t0))
    # print "\nPredicated result for picture_1 name: ", pic1_pred_name
    # for i in range(1,3): print ("\n")

    # Display the picture
    # plt.figure(1)
    # plt.title(pic1_pred_name)
    # plt.subplot(111)
    # plt.imshow(X_test_pic1_for_display)
    # plt.show()


    ###############################################################################
    # Qualitative evaluation of the predictions using matplotlib
    # import matplotlib.pyplot as plt

    # def plot_gallery(images, titles, face_dim, n_row=3, n_col=4):
    #     """Helper function to plot a gallery of portraits"""
    #     plt.figure(figsize=(1.8 * n_col, 2.4 * n_row))
    #     plt.subplots_adjust(bottom=0, left=.01, right=.99, top=.90, hspace=.35)
    #     for i in range(n_row * n_col):
    #         plt.subplot(n_row, n_col, i + 1)
    #         plt.imshow(images[i].reshape(face_dim), cmap=plt.cm.gray)
    #         plt.title(titles[i], size=12)
    #         plt.xticks(())
    #         plt.yticks(())


    # # plot the result of the prediction on a portion of the test set

    # def title(y_pred, y_test, face_profile_names, i):
    #     pred_name = face_profile_names[y_pred[i]].rsplit(' ', 1)[-1]
    #     true_name = face_profile_names[y_test[i]].rsplit(' ', 1)[-1]
    #     return 'predicted: %s\ntrue:      %s' % (pred_name, true_name)

    # prediction_titles = [title(y_pred, y_test, face_profile_names, i)
    #                      for i in range(y_pred.shape[0])]

    # plot_gallery(X_test, prediction_titles, face_dim)

    # # plot the gallery of the most significative eigenfaces

    # eigenface_titles = ["eigenface %d" % i for i in range(eigenfaces.shape[0])]
    # plot_gallery(eigenfaces, eigenface_titles, face_dim)

    # plt.show()


    return clf, pca


def build_SVC(face_profile_data, face_profile_name_index, face_dim):

    X = face_profile_data
    y = face_profile_name_index

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    # Compute a PCA (eigenfaces) on the face dataset (treated as unlabeled
    # dataset): unsupervised feature extraction / dimensionality reduction
    n_components = 150 # maximum number of components to keep

    print("\nExtracting the top %d eigenfaces from %d faces" % (n_components, X_train.shape[0]))

    pca = RandomizedPCA(n_components=n_components, whiten=True).fit(X_train)
    eigenfaces = pca.components_.reshape((n_components, face_dim[0], face_dim[1]))

    # This portion of the code is used if the data is scarce, it uses the number
    # of imputs as the number of features
    # pca = RandomizedPCA(n_components=None, whiten=True).fit(X_train)
    # eigenfaces = pca.components_.reshape((pca.components_.shape[0], face_dim[0], face_dim[1]))

    print("\nProjecting the input data on the eigenfaces orthonormal basis")
    X_train_pca = pca.transform(X_train)
    X_test_pca = pca.transform(X_test)

    # Train a SVM classification model

    print("\nFitting the classifier to the training set")
    param_grid = {'C': [1e3, 5e3, 1e4, 5e4, 1e5],
                  'gamma': [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.1], }
    # clf = GridSearchCV(SVC(kernel='rbf', class_weight='balanced'), param_grid)

    # Best Estimator found using Radial Basis Function Kernal:
    clf = SVC(C=1000.0, cache_size=200, class_weight='balanced', coef0=0.0,
  decision_function_shape=None, degree=3, gamma=0.0001, kernel='rbf',
  max_iter=-1, probability=False, random_state=None, shrinking=True,
  tol=0.001, verbose=False)
    # Train_pca with Alex Test Error Rate:  0.088424437299
    # Train_pca with Alex Test Recognition Rate:  0.911575562701

    clf = clf.fit(X_train_pca, y_train)
    # print("\nBest estimator found by grid search:")
    # print(clf.best_estimator_)

    ###############################################################################
    # Quantitative evaluation of the model quality on the test set
    print("\nPredicting people's names on the test set")
    t0 = time()
    y_pred = clf.predict(X_test_pca)
    print("\nPrediction took %s per sample on average" % ((time() - t0)/y_pred.shape[0]*1.0))

    # print "predicated names: ", y_pred
    # print "actual names: ", y_test
    error_rate = errorRate(y_pred, y_test)
    print ("\nTest Error Rate: %0.4f %%" % (error_rate * 100))
    print ("Test Recognition Rate: %0.4f %%" % ((1.0 - error_rate) * 100))

    return clf, pca


def predict(clf, pca, img, face_profile_names):

    img = img.ravel()
    # Apply dimentionality reduction on img, img is projected on the first principal components previous extracted from the Yale Extended dataset B.
    principle_components = pca.transform(img[0])
    pred = clf.predict(principle_components)[0]
    name = face_profile_names[pred]
    return name

def errorRate(pred, actual):

    if pred.shape != actual.shape: return None
    error_rate = np.count_nonzero(pred - actual)/float(pred.shape[0])
    return error_rate
