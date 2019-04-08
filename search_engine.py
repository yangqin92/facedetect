#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/6 16:11
# @Author  : Gehen
# @Site    : 
# @File    : search_engine.py
# @Software: PyCharm Community Edition

from sklearn.neighbors import LSHForest, NearestNeighbors
import numpy as np
import pickle as pkl
import time
from scipy import spatial
# import tables as tb
import os


class Search_engin(object):
    def __init__(self, feature_array, method='exact', n_neighbors=1, n_estimators=40,
                 n_candidates=50, algorithm='ball_tree', metric='euclidean'):
        if method == 'exact':
            self.method = 'exact'
            self.engin = NearestNeighbors(n_neighbors=n_neighbors,
                                          algorithm=algorithm, metric=metric)
        elif method == 'approx':
            self.method = 'approx'
            self.engin = LSHForest(n_estimators=n_estimators, n_candidates=n_candidates,
                                   n_neighbors=n_neighbors)
        else:
            self.method = None
            raise Exception('Undefined method')
        self.feas = feature_array

    def train(self):
        print('begin to build search engine')
        #start = time.time()
        feas = self.feas
        if self.method == 'exact':
            fea_norm = np.linalg.norm(feas, axis=1)[:, np.newaxis]
            feas = feas / fea_norm
            self.engin.fit(feas)
        elif self.method == 'approx':
            self.engin.fit(feas)
        else:
            raise Exception('Undefined method')
        del feas

    def search(self, queris):
        if self.method == 'exact':
            queris = queris / np.linalg.norm(queris)
            distances, indices = self.engin.kneighbors(queris)
        elif self.method == 'approx':
            distances, indices = self.engin.kneighbors(queris)
        else:
            raise Exception('Undefined method')

        return indices

if __name__ == '__main__':
    #index_path = './data/index_enter.pkl'
    #feature_path = './data/database.npy'
    feature_path = './data/database_enter.npy'

    #with open(index_path, 'rb') as f:
        #index_dict = pkl.load(f)
    feature_data = np.load(feature_path)

    print(feature_data)
    search_engine = Search_engin(feature_data)
    search_engine.train()
    idx_list = search_engine.search(feature_data[0])
    print(idx_list)
    idx_list = [idx_list[0][i] for i in range(idx_list.shape[1])]


    print(idx_list)
    score = 1 - spatial.distance.cosine(feature_data[0], feature_data[0])

    print(score)




