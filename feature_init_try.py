#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/6/8 12:50
# @Author  : lijing
# @Site    :
# @File    : feature_init.py
# @Software: PyCharm Community Edition


import cv2
import os
import numpy as np
import pickle as pkl
from glob import glob
from feature_extractor2 import Extractor,NaiveDlib
from config import feature_pic_path_enter
from preprocess.crop_util import crop_rotate_v2
from preprocess.image_preprocess import proc_img
from datetime import datetime
index_path = './data/index_enter.pkl'
#feature_pic_path_enter = r'E:\python\Face_Verify2018.5.3\user_pic'


class Feature_Init():
    def __init__(self):
        self.ext_model_path = './model/facenet/inception-ring-1024.pb'
        self.feature_path_enter = './data/database_enter.npy'
        self.index_path_enter = './data/index_enter.pkl'
        self.image_path_enter = feature_pic_path_enter


        self.feature_data = np.asarray([])  # 转换为矩阵形式
        self.index_dict = {}
        self.naivedlib = NaiveDlib()
        self.extractor = Extractor(self.ext_model_path, gpu_fraction=0.5)
       # temp = np.ones((1, 112, 96, 1))
        #self.extractor.extract_feature(im_arr=temp)

    def extract_feature_enter(self):
        if os.path.exists(self.feature_path_enter) and os.path.exists(self.index_path_enter):
            try:
                with open(self.index_path_enter,'rb') as f:
                    self.index_dict = pkl.load(f)
                self.feature_data = np.load(self.feature_path_enter)
            except:
                self.index_dict = {}
                self.feature_data = np.asarray([])
        img_list = os.listdir(self.image_path_enter)#返回指定的文件夹包含的文件或文件夹的名字的列表
        img_len = len(img_list)
        #print(img_list)
        name_list = [item.split('.')[0] for item in img_list]
        #print(name_list)
        key_list = list(self.index_dict.keys())

        if self.feature_data.shape[0] != len(self.index_dict.keys()):
            self.index_dict = {}
            self.feature_data = np.asarray([])
        for key in key_list:
            if key not in name_list:
                self.index_dict = {}
                self.feature_data = np.asarray([])
                break
        if len(self.index_dict.values()) > 0:
            dict_index = max(self.index_dict.values())
        else:
            dict_index = 0
        count = 1
        if len(self.index_dict.keys())==0:
            count = 0
        write_flag = 0
        img_list.sort()
        for img in img_list:
            name_value = img.split('.')[0]
            if name_value not in list(self.index_dict.keys()):
                self.index_dict[name_value] = dict_index+count
                # self.index_dict[name_value] = count
                image = cv2.imread(os.path.join(self.image_path_enter,img))
                im_arr = self.extractor.preprocess_imgage(image, self.naivedlib)
                feature = self.extractor.extract_feature(im_arr=im_arr)
                feature = feature/np.linalg.norm(feature)
                if self.feature_data.ndim>1:# 维度
                    self.feature_data = np.vstack((self.feature_data,feature))
                else:
                    self.feature_data = feature[np.newaxis,:]
                count += 1
                write_flag = 1

        with open('./data/flag.txt','w+') as f:
            f.write(str(write_flag))
        with open(self.index_path_enter,'wb') as f:
            pkl.dump(self.index_dict,f)
        with open(self.feature_path_enter,'wb') as f:
            self.feature_data = np.asarray(self.feature_data)
            np.save(f,self.feature_data)

        print ('Feature init finished')

    def setimage(self,image1, p_id ):#更新图像时替换feature
        #image_first = "./user_pic/{}.bmp".format(p_id)
        #image1 = cv2.imread(image_url)
        #image2 = cv2.imread(image_first)
        name = p_id
        with open(self.index_path_enter, 'rb') as f:
            self.index_dict = pkl.load(f)
        with open(self.feature_path_enter, 'rb') as f:
            self.feature_data = np.load(f)
        value = self.index_dict[name]
        print(value)
        feature0 = self.feature_data[value]
        print (feature0)
        im_arr = self.extractor.preprocess_imgage(image1, self.naivedlib)
        feature = self.extractor.extract_feature(im_arr=im_arr)
        feature = feature / np.linalg.norm(feature)
        print(feature)
        self.feature_data[value] = feature
        with open('./data/database_enter.npy', 'wb') as f:
            self.feature_data = np.asarray(self.feature_data)
            np.save(f, self.feature_data)



if __name__=='__main__':
    currentTime = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    print(currentTime)


    init_fea = Feature_Init()
    init_fea.extract_feature_enter()
    print(datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
    feature_path  = './data/database_enter.npy'
    with open(index_path, 'rb') as f:

        index_dict = pkl.load(f)
    with open(feature_path, 'rb') as f:
         feature_path = np.load(f)
    print(index_dict)
    print(feature_path)
   # image1 = cv2.imread("./user_pic/18392886034.bmp")
    #init_fea.setimage(image1)