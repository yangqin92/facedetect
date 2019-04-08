# -*- coding: utf-8 -*-
# Form implementation generated from reading ui file 'face_verification_2018_5_10.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# 摄像头人脸识别，识别未知和已知访客，并保存当前捕捉到的人脸图片（保存在image_save)
# 人数统计：同一个人在10秒内多次识别作为一次
# 海康摄像头：79行和89行改配置
# 推送：socketio尝试失败
# WARNING! All changes made in this file will be lost!


import cv2, sys, os, time
# import math
import shutil
import time
#import subprocess
import numpy as np
from multiprocessing import Process, Queue  # 多进程
#from PyQt4 import QtCore, QtGui
from feature_extractor2 import Extractor, NaiveDlib

from preprocess.crop_util_search import crop_rotate_part
from preprocess.image_preprocess import proc_img
from collections import deque
#from xlwt import *  # 数据导出到表格需要使用
from search_engine import Search_engin
from config import *
from datetime import datetime, timedelta
#import wmi
#import hashlib
import pickle as pkl
from scipy import spatial
import dlib
import pymysql
# from person_infomanage_api import getperson_tables

import json
import requests





# 定义的全局变量

License = ""
VIDEO_IMAGE = Queue()  # 放从摄像头读到的帧用于display_probe_image


# probe_image = Queue()#放从display_probe_image保存的帧用于verify


class Face_Verification(object):
    def __init__(self):
        ext_model_path = './model/facenet/inception-ring-1024.pb'
        # self.video_capture = cv2.VideoCapture(camera_Id)
        # self.video_capture = cv2.VideoCapture(HKcam)
        # self.is_camera_on = True
        self.id_image = None
        self.id_image2 = None
        self.id_image1_2 = None
        # self.probe_image = None
        self.ID_label = 0
        self.count = 0
        self.ID_lib = {}
        self.ID_name = {}
        self.feature_data = None
        self.index_dict = None
        self.unknownum = 0  # 10秒内未知人员数
        self.knownum = 0  # 10秒内已知人员数

        self.unknown_feature_read()

        self.naivedlib = NaiveDlib()
        self.extractor = Extractor(ext_model_path, gpu_fraction=0)  # gpu_fraction显存占用比例
        temp = np.ones((5, 112, 96, 1))
        self.extractor.extract_feature(im_arr=temp)
        self.query = deque(maxlen=2)

        self.search_train()

    def search_train(self):  # 已知访客搜索初始化 后面补充10秒清空时加入这个为了人员信息管理时的更新，先判断feature_change==1
        with open('./data/index_enter.pkl', 'rb') as f:
            self.index_dict = pkl.load(f)
        with open('./data/database_enter.npy', 'rb') as f:
            self.feature_data = np.load('./data/database_enter.npy')
        self.search_eign = Search_engin(self.feature_data)
        self.search_eign.train()

    def unknown_feature_read(self):
        # self.datetime = datetime.now().strftime('%Y_%m_%d')
        # self.unknownfeature_path = './data/unknown_feature.npy'
        # self.unknown_pic_path = './image_saved/{}/unknown'.format(self.datetime)
        # self.known_pic_path = './image_saved/{}/known'.format(self.datetime)
        self.unknownfeature = np.asarray([])  # 10秒内未知特征
        self.unknownum = 0
        self.knownum = 0
        self.knownlist = []  # 10秒内已知人名
        self.summary = {}  # 10秒内统计信息

    def wait_clean(self):  # 10秒数据清除和人数保存

        with open('feature_change.txt', 'r') as f:
            data = f.readline()
            feature_change = int(data)
        if feature_change == 1:
            self.search_train()
            feature_change = 0
            with open('feature_change.txt', 'w+') as f:
                f.write(str(feature_change))
        self.knownum = 0
        self.unknownum = 0
        self.unknownfeature = np.asarray([])
        self.knownlist = []

    def insert_summary(self):  # 10秒内有人进来则将这10秒的第一个人进来的时间，已知访客的p_id,已知访客人数，未知访客数，总数插入
        comtime = self.summary["comtime"]
        knownum = self.knownum
        unknownum = self.unknownum
        num = knownum + unknownum

        conn = pymysql.connect(host='localhost',
                               port=3306,
                               user='root',
                               passwd='1234567',
                               db="face_info",
                               charset="utf8"
                               )
        c = conn.cursor()
        try:
            for i in range(self.knownum):
                p_id = self.knownlist[i]

                sql = '''insert into num_info
                                                             (comtime,
                                                              p_id, 
                                                              knownum,
                                                              unknownum,
                                                              num)
                                        VALUES ('%s','%s', '%d',  '%d',  '%d')   ''' % (
                    comtime, p_id, knownum, unknownum, num)
                c.execute(sql)
                conn.commit()
            print("Table inserted successfuly")
            c.close()
            conn.close()

        except:
            print("Table inserted failed")

    def verify(self, thresh):  # 识别比对
        global VIDEO_IMAGE
        global isPass
        new_person = 0  # newperson = 1时则说明有人来
        knownflag = 0
        unknownflag = 0
        currentunknownum = 0
        currentknownum = 0
        idname = []  # 可显示id照片的编号列表
        currentDate = datetime.now().strftime('%Y_%m_%d')
        currentTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        currentTime_img = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

        # if self.pic_time != None and (datetime.datetime.now() - self.pic_time).seconds > pic_time:
        # self.image_clear()
        image1 = None
        for i in range(VIDEO_IMAGE.qsize()):
            image1 = VIDEO_IMAGE.get()
        image1 = cv2.imread('cut0.jpg')  # 加载图片测试
        #cv2.imwrite('cut0.jpg', image1)
        if image1 is not None:
            print('get image')
            #image1 = image1[:, 250:1500]
            image1 = cv2.flip(image1, 1)
            width = int(image1.shape[1] / 2)
            height = int(image1.shape[0] / 2)
            image = cv2.resize(image1.copy(), (width, height))
            #cv2.imwrite('cut.jpg', image1)



            try:
                start = time.time()
                bboxs = self.naivedlib.getALLFaces(image)
                end = time.time()
                print('bbox detect took ')
                bboxs = [dlib.rectangle(int(bbox.left() * downsample_ratio), int(bbox.top() * downsample_ratio),
                                        int(bbox.right() * downsample_ratio), int(bbox.bottom() * downsample_ratio))
                         for bbox in bboxs]
                #facenum = len(bboxs)
                print('\tbbox took {}'.format(end - start))
                if bboxs is not None:
                    new_person = 1
                    print(time.strftime('%H:%M:%S', time.localtime(time.time())))
                    for bbox in bboxs:
                        # 对每个人脸进行操作
                        print('bbox is detected')
                        query = []

                        left_eye, right_eye = self.naivedlib.get_eyes(image1, bbox)
                        start = time.time()
                        save_croped, crop_image = crop_rotate_part(image1[:, :, ::-1], bbox, left_eye, right_eye,
                                                                   bbox.width() * 0.895)
                        save_croped = cv2.cvtColor(save_croped, cv2.COLOR_BGR2RGB)

                        # bbox_temp = [bbox.left(),bbox.top(),bbox.right(),bbox.bottom()]
                        # crop_image = crop_only(image1,bbox_temp)
                        # cv2.imwrite('image.jpg',crop_image)
                        end = time.time()
                        print('\tpreprocess took {}'.format(end - start))

                        flip_image = cv2.flip(crop_image.copy(), 1)
                        crop_image = proc_img(crop_image, is_whiten=False)
                        flip_image = proc_img(flip_image, is_whiten=False)
                        query.append(crop_image[0])
                        query.append(flip_image[0])
                        prob_image = np.asarray(query)

                        start = time.time()
                        feature = self.extractor.extract_feature(prob_image)
                        end = time.time()
                        print('\textract feature took {}'.format(end - start))
                        feature = feature / np.linalg.norm(feature)
                        idx_list = self.search_eign.search(feature)  # 获取搜索后的排列
                        idx_list = [idx_list[0][i] for i in range(idx_list.shape[1])]
                        score_list = []
                        name_list = []
                        for idx in idx_list:
                            score = 1 - spatial.distance.cosine(feature, self.feature_data[int(idx)])
                            name = {value: key for key, value in self.index_dict.items()}[int(idx)]
                            score_list.append(score)
                            name_list.append(name)
                        #print(name_list)
                        #print(score_list)

                        score = 1 - spatial.distance.cosine(feature, self.feature_data[int(idx_list[0])])
                        thresh = float(thresh)
                        # print(thresh)
                        if score > thresh:
                            knownflag = 1
                            name = name_list[0]
                            if self.knownum == 0:
                                self.knownum = 1
                                self.summary["comtime"] = currentTime
                                self.knownlist.append(name)
                                if not os.path.exists('./image_saved/{}'.format(currentDate)):
                                    os.mkdir('./image_saved/{}'.format(currentDate))
                                    os.mkdir('./image_saved/{}/unknown'.format(currentDate))
                                    os.mkdir('./image_saved/{}/known'.format(currentDate))
                                cv2.imwrite('./image_saved/{}/known/{}_{}.jpg'.format(currentDate, currentTime_img,
                                                                                      name),
                                            save_croped)
                                idname.append(name)  # 当前帧中的已知访客name
                                print("欢迎" + name)
                                # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                            else:

                                if name not in self.knownlist:
                                    self.knownlist.append(name)
                                    self.knownum = self.knownum + 1
                                    cv2.imwrite('./image_saved/{}/known/{}_{}.jpg'.format(currentDate, currentTime_img,
                                                                                          name),
                                                save_croped)
                                    idname.append(name)  # 当前帧中的已知访客name

                                    print("欢迎" + name)
                                    # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

                        else:
                            unknownflag = 1
                            if self.unknownum == 0:
                                print("第一个未知人员")
                                currentunknownum = currentunknownum + 1
                                self.unknownum = 1
                                if self.summary == []:
                                    self.summary["comtime"] = currentTime
                                if not os.path.exists('./image_saved/{}'.format(currentDate)):
                                    os.mkdir('./image_saved/{}'.format(currentDate))
                                    os.mkdir('./image_saved/{}/unknown'.format(currentDate))
                                    os.mkdir('./image_saved/{}/known'.format(currentDate))

                                cv2.imwrite('./image_saved/{}/unknown/{}_{}.jpg'.format(currentDate, currentTime_img,
                                                                                        self.unknownum), save_croped)
                                self.unknownfeature = feature[np.newaxis, :]

                            else:
                                unthresh = 0.5
                                self.search_eign_unknown = Search_engin(self.unknownfeature)  # 未知访客搜索
                                self.search_eign_unknown.train()
                                unknown_idx = self.search_eign_unknown.search(feature)
                                unknown_idx = [unknown_idx[0][i] for i in range(unknown_idx.shape[1])]
                                print(unknown_idx)
                                uscore = 1 - spatial.distance.cosine(feature, self.unknownfeature[int(unknown_idx[0])])
                                print(uscore)
                                if uscore < unthresh:  # 第一次识别出该未知人员
                                    self.unknownum = self.unknownum + 1
                                    currentunknownum = currentunknownum + 1
                                    # self.unknownlist[self.unknownum] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    cv2.imwrite(
                                        './image_saved/{}/unknown/{}_{}.jpg'.format(currentDate, currentTime_img,
                                                                                    self.unknownum), save_croped)
                                    self.unknownfeature = np.vstack((self.unknownfeature, feature))
                else:
                    new_person = 0
            except:
                pass
        else:
            print("图片为空！")
        return (new_person)

    def push_summary(self):  # 推送汇总
        dict_push = {}
        if self.knownum != 0:
            dict_push["known"] = "{}".format(self.knownum)
            dict_push["unknown"] = "{}".format(self.unknownum)
            for i in range(self.knownum):
                p_id = self.knownlist[i]
                result = getperson_tables(p_id)

                #image_url = result[0][3]
                image_url = "http://" + host_ip + ":5000" + "/user_pic/{}".format(p_id)
                count, lasttime = select_tables(p_id)

                dict_push["person_{}".format(i)] = {"count": "{}".format(count), "lasttime": "{}".format(lasttime),
                                                    "image": image_url}
        else:
            # 全是未知人员
            dict_push["known"] = 0
            dict_push["unknown"] = "{}".format(self.unknownum)
        return (dict_push)


def camera_reader(queue):
    video_capture = cv2.VideoCapture(HKcam )  # 调试海康时换成HKcam
    count = 0
    while True:
        ret, image0 = video_capture.read()
        count = count + 1
        # print (count)
        if ret:
            if count % 1 == 0:
                queue.put(image0)
                #cv2.namedWindow("hkcam", 0)
                #cv2.resizeWindow("hkcam", 640, 480)
                cv2.imshow("hkcam", image0)

                if cv2.waitKey(3) & 0xFF == ord('q'):
                    break

        else:
            video_capture = cv2.VideoCapture(HKcam )  # 调试海康时换成HKcam


def create_tables(dbname):  # 创建表num_info，
    conn = pymysql.connect(host='localhost',
                           port=3306,
                           user='root',
                           passwd='1234567',
                           db="face_info",
                           charset='utf8'
                           )
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE if not exists num_info
                                                         (id int auto_increment primary key,
                                                          comtime  datetime,
                                                          p_id varchar(12), 
                                                          knownum int,
                                                          unknownum int,
                                                          num int);''')
        print("Table created successfuly")
    except:
        print("Table created failed")
    conn.commit()
    c.close()
    conn.close()


def getperson_tables(p_id):  # 查找人脸信息
    conn = pymysql.connect(host='localhost',
                           port=3306,
                           user='root',
                           passwd='1234567',
                           db="face_info",
                           charset='utf8'
                           )
    c = conn.cursor()
    try:
        # c.execute('''update person_info set p_id = '%s' where p_id = '%s' ''' % (p_id, p_id0))
        c.execute('''select * from person_info where p_id = '%s' ''' % p_id)
        results = c.fetchall()
        # print (results)
        if results ==():
            return None
        # print("Table updated successfuly")
        conn.commit()
        c.close()
        conn.close()
        return results
    except:
        print("Table selected failed")
        return 1


def select_tables(p_id):  # 在num_info中查找该p_id的出现的次数和最近时间
    conn = pymysql.connect(host='localhost',
                           port=3306,
                           user='root',
                           passwd='1234567',
                           db="face_info",
                           charset='utf8'
                           )
    c = conn.cursor()

    try:
        c.execute('''select *  from num_info where p_id = '%s'  ''' % p_id)
        results = c.fetchall()
        if results ==():
            return(0,0)
        else:
            c.execute('''select count(*)  from num_info where p_id = '%s' group by p_id  ''' % p_id)
            results = c.fetchall()
            count = results[0][0]
            # print(count)

            c.execute('''select max(comtime)  from num_info where p_id = '%s'   ''' % p_id)
            results = c.fetchall()
            lasttime = results[0][0]
            # print(results[0][0])
            conn.commit()
            c.close()
            conn.close()
            return (count, lasttime)
    except:
        print("Table selected failed")




if __name__ == "__main__":
    global thresh
    global video_capture
    waitcount = 0
    dbname = "face_info"
    #create_tables(dbname) #创建num_info 数据库保存人脸识别信息

    face = Face_Verification()
    p = Process(target=camera_reader, args=(VIDEO_IMAGE,))
    p.start()
    #faceverify_post_url = 'http://127.0.0.1:3000/vms/facedetect'#在配置文件

    while (1):
        new_person = face.verify(thresh)
        waitcount = waitcount + 1
        if waitcount % 10 == 0:  # 10秒内重复识别只计一次，同时也就是10秒内被一起识别的皆为随从人员
            if new_person == 1:
                print("推送")
                push_info = face.push_summary()
                s = json.dumps(push_info)
                r = requests.get(faceverify_post_url, data=s)
                face.insert_summary()
                face.wait_clean()

        time.sleep(2)
        if 0xFF == ord('q'):
            break
    video_capture.release()
    cv2.destroyAllWindows()







