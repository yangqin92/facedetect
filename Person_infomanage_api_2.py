# -*- coding: utf-8 -*-
# 人脸信息增删改，连接mysql,db="face_info",table="person_info"
# 增加和删除操作触发人脸图片初始化，修改对图片替换特征值
# 遗留问题：appid的验证需要在商定
# 静态图片人脸识别，可识别同一图片中的多张人脸（给定图片路径）--2018/6/21
# 统计信息根据时间查询,table="num_info"
# @Time    : 2018/8/11 15:00
# @Author  : lijing
# @File    : Person_infomanage_api_2.py
# @Software: PyCharm Community Edition
# ---------------最新，后期只需改图片云地址解析（现在是七牛云默认）----



from flask import Flask
import urllib.request

import requests
import json
import os
import pymysql
from flask import Flask,make_response
from flask import request
from flask import redirect
from flask import jsonify
from feature_init_try import Feature_Init
from PIL import Image
import cv2
import numpy as np

from feature_extractor2 import Extractor,NaiveDlib
from preprocess.crop_util import crop_rotate_v2
from preprocess.crop_util_search import crop_rotate_part
from preprocess.image_preprocess import proc_img
from loadpic import loadimage, urls

from search_engine import Search_engin
from config import *


from datetime import datetime , timedelta

#import wmi
#import hashlib
import pickle as pkl
from scipy import spatial
import dlib
import time

app = Flask(__name__)
init_fea = Feature_Init()


naivedlib = NaiveDlib()
extractor = Extractor(ext_model_path, gpu_fraction=0)

thresh = 0.55
global feature_change

def create_tables(dbname): #创建表person_info
    conn = pymysql.connect(host = 'localhost',
                           port = 3306,
                           user = 'root',
                           passwd = '1234567',
                           db="face_info",
                           charset='utf8'
                           )
    c = conn.cursor()
    try:
        c.execute('''CREATE TABLE if not exists person_info
                                                         (id int auto_increment primary key,
                                                          p_id varchar(11),
                                                          name varchar(12),
                                                          image_url varchar(60),
                                                          tag varchar(20));''')
        print("Table created successfuly")
    except:
        print ("Table created failed")
    conn.commit()
    c.close()
    conn.close()

def newperson_tables(p_id, name,image_url,tag):# 添加人脸
    conn = pymysql.connect(host = 'localhost',
                           port = 3306,
                           user = 'root',
                           passwd = '1234567',
                           db="face_info",
                           charset = "utf8"
                           )
    c = conn.cursor()
    try:
        sql = '''insert into person_info
                                       (p_id,
                                        name, 
                                        image_url,
                                        tag)
                  VALUES ('%s', '%s', '%s', '%s')   ''' % (p_id, name, image_url,tag)

        c.execute(sql)
        print("Table added successfuly")
        conn.commit()
        c.close()
        conn.close()
        return 0

    except:
        print ("Table added failed")
        return 1


def delperson_tables(p_id):#删除人脸，同时删除feature_pic_path_enter中的人脸图片
    conn = pymysql.connect(host = 'localhost',
                           port = 3306,
                           user = 'root',
                           passwd = '1234567',
                           db="face_info",
                           charset='utf8'
                           )
    c = conn.cursor()
    try:
        c.execute('''delete from person_info where p_id = '%s' ''' % p_id)
        print("Table deleted successfuly")
        conn.commit()
        c.close()
        conn.close()
        return 0
    except:
        print ("Table deleted failed")
        return 1

def setperson_tables(p_id, name , image_url,tag ):#更新人脸信息
    conn = pymysql.connect(host = 'localhost',
                           port = 3306,
                           user = 'root',
                           passwd = '1234567',
                           db="face_info",
                           charset='utf8'
                           )
    c = conn.cursor()
    try:
        #c.execute('''update person_info set p_id = '%s' where p_id = '%s' ''' % (p_id, p_id0))
        c.execute('''update person_info set name = '%s' , image_url = '%s' , tag = '%s' where p_id = '%s' ''' % ( name, image_url,tag, p_id))
        print("Table updated successfuly")
        conn.commit()
        c.close()
        conn.close()
        return 0
    except:
        print ("Table updated failed")
        return 1

def getperson_tables(p_id):#查找人脸信息
    conn = pymysql.connect(host = 'localhost',
                           port = 3306,
                           user = 'root',
                           passwd = '1234567',
                           db="face_info",
                           charset='utf8'
                           )
    c = conn.cursor()
    try:
        #c.execute('''update person_info set p_id = '%s' where p_id = '%s' ''' % (p_id, p_id0))
        c.execute('''select * from person_info where p_id = '%s' ''' % p_id)
        results = c.fetchall()
        #print (results)


        #print("Table updated successfuly")
        conn.commit()
        c.close()
        conn.close()
        return results
    except:
        print ("Table selected failed")
        return 1


def verify_img(img):
    image1 = img
    p_id_list = []
    api_unknown = 0
    if image1 is not None:
        with open('./data/index_enter.pkl', 'rb') as f:
            index_dict = pkl.load(f)
        with open('./data/database_enter.npy', 'rb') as f:
            feature_data = np.load('./data/database_enter.npy')
        search_eign = Search_engin(feature_data)
        search_eign.train()
        #print('get image')
        image1 = cv2.flip(image1, 1)
        width = int(image1.shape[1] / 2)
        height = int(image1.shape[0] / 2)
        image = cv2.resize(image1.copy(), (width, height))

        try:
            bboxs = naivedlib.getALLFaces(image)
            print('bbox detect took ')
            bboxs = [dlib.rectangle(int(bbox.left() * downsample_ratio), int(bbox.top() * downsample_ratio),
                                    int(bbox.right() * downsample_ratio), int(bbox.bottom() * downsample_ratio))
                     for bbox in bboxs]
            facenum = len(bboxs)
            if bboxs is not None:
                for bbox in bboxs:
                    # 对每个人脸进行操作
                    #print('bbox is detected')
                    query = []
                    left_eye, right_eye = naivedlib.get_eyes(image1, bbox)
                    start = time.time()
                    save_croped, crop_image = crop_rotate_part(image1[:, :, ::-1], bbox, left_eye, right_eye,
                                                               bbox.width() * 0.895)
                    save_croped = cv2.cvtColor(save_croped, cv2.COLOR_BGR2RGB)
                    end = time.time()
                    print('\tpreprocess took {}'.format(end - start))
                    flip_image = cv2.flip(crop_image.copy(), 1)
                    crop_image = proc_img(crop_image, is_whiten=False)
                    flip_image = proc_img(flip_image, is_whiten=False)
                    query.append(crop_image[0])
                    query.append(flip_image[0])
                    prob_image = np.asarray(query)

                    start = time.time()
                    feature = extractor.extract_feature(prob_image)
                    end = time.time()
                    print('\textract feature took {}'.format(end - start))
                    feature = feature / np.linalg.norm(feature)
                    idx_list = search_eign.search(feature)  # 获取搜索后的排列
                    idx_list = [idx_list[0][i] for i in range(idx_list.shape[1])]
                    score_list = []
                    name_list = []
                    for idx in idx_list:
                        score = 1 - spatial.distance.cosine(feature, feature_data[int(idx)])
                        name = {value: key for key, value in index_dict.items()}[int(idx)]
                        score_list.append(score)
                        name_list.append(name)
                    #print(name_list)
                    #print(score_list)
                    score = 1 - spatial.distance.cosine(feature, feature_data[int(idx_list[0])])
                    #print(thresh)
                    if score > thresh:
                        p_id_list.append(name_list[0])
                    else:
                        api_unknown = api_unknown + 1

        except:
            pass
        #print(p_id_list)
    return (p_id_list, api_unknown)

def select_count(begintime, endtime):  # 在num_info中查找该时间段内总人数
    conn = pymysql.connect(host='localhost',
                           port=3306,
                           user='root',
                           passwd='1234567',
                           db="face_info",
                           charset='utf8'
                           )
    c = conn.cursor()

    try:
        c.execute('''select sum(num) from num_info where id in
                         (select min(id) from num_info where comtime between '%s' and '%s' 
                                       group by comtime) ''' % (begintime, endtime))

        results = c.fetchall()

        count = results[0][0]


        conn.commit()
        c.close()
        conn.close()
        return (count)
    except:
        print("Table selected failed")


def select_tables():  # 在num_info中查找最大和最小时间
    conn = pymysql.connect(host='localhost',
                           port=3306,
                           user='root',
                           passwd='1234567',
                           db="face_info",
                           charset='utf8'
                           )
    c = conn.cursor()

    try:
        c.execute('''select max(comtime)  from num_info '''  )
        results = c.fetchall()
        max_time = results[0][0]
        print(max_time)
        c.execute('''select min(comtime)  from num_info  ''' )
        results = c.fetchall()
        min_time = results[0][0]
        print(min_time)
        conn.commit()
        c.close()
        conn.close()
        return (max_time, min_time)
    except:
        print("Table selected failed")

@app.route('/face/newperson' , methods=['GET', 'POST'])
def newperson():
    if request.method == 'POST':
        a = request.get_data()
        dict1 = json.loads(a)
        if dict1["appid"] == "ZQKJ2018":
            if len(dict1["data"]["p_id"]) == 11:
                p_id = dict1["data"]["p_id"]
                result = getperson_tables(p_id)
                if result == ():
                    if dict1["data"]["name"]:
                        name = dict1["data"]["name"]
                        if dict1["data"]["image"]:
                            image_url = dict1["data"]["image"]
                            print(image_url)
                            save_url = urls(image_url)
                            #urllib.request.urlretrieve(image_url, fileout)
                            #print(image_url)
                            loadimage(image_url,p_id)
                            tag = ""
                            try:
                                if dict1["data"]["tag"]:
                                    tag = dict1["data"]["tag"]
                            except:
                                tag = ""
                            if tag == "":
                                tag = None
                            code = newperson_tables(p_id, name, save_url, tag)
                            if code == 0:
                                    dict_success = {"data": {"p_id": "{}".format(p_id)}, "code": int(0), "msg": "success"}
                                    # 重新初始化人脸信息
                                    init_fea.extract_feature_enter()
                                    feature_change = 1
                                    with open('feature_change.txt', 'w+') as f:
                                        f.write(str(feature_change))
                                    return json.dumps(dict_success, ensure_ascii=False)
                            else:
                                    dict_error = {"code": int(1), "msg": "添加失败请检查数据库是否连接！"}
                                    return json.dumps(dict_error, ensure_ascii=False)

                        else:
                            dict_error = {"code": int(1), "msg": "请给出image参数！"}
                            return json.dumps(dict_error, ensure_ascii=False)
                    else:
                        dict_error = {"code": int(1), "msg": "请给出name参数！"}
                        return json.dumps(dict_error, ensure_ascii=False)
                else:
                    dict_error = {"code": int(1), "msg": "该号码已经注册！"}
                    return json.dumps(dict_error, ensure_ascii=False)
            else:
                dict_error = {"code": int(1), "msg": "手机号码错误！"}
                return json.dumps(dict_error, ensure_ascii=False)
        else:
            dict_error = {"code": int(1), "msg": "验证无效！"}
            return json.dumps(dict_error, ensure_ascii=False)
    else:
        dict_error = {"code":int(1),"msg":"只接受post请求！"}
        return json.dumps(dict_error, ensure_ascii=False)

@app.route('/face/delperson', methods=['GET', 'POST'])#先删除user_pic下的图片再初始化feature再连接数据库删除记录
def delperson():
        if request.method == 'POST':
            a = request.get_data()
            dict1 = json.loads(a)
            #print(dict1)
            if dict1["appid"] == "ZQKJ2018":
                if len(dict1["data"]["p_id"]) == 11:
                    p_id = dict1["data"]["p_id"]
                    results = getperson_tables(p_id)
                    if results != 1:
                        if results == ():
                            dict_error = {"code": int(1), "msg": "未录入此人信息！"}
                            return json.dumps(dict_error, ensure_ascii=False)
                        else:
                            image = results[0][3]
                            image0 = image.split('.')[1] #分离得到后缀
                            image_url = "./user_pic/{}.{}".format(p_id,image0)
                    else:
                        dict_error = {"code": int(1), "msg": "获取失败请检查数据库是否连接！"}
                        return json.dumps(dict_error, ensure_ascii=False)

                    if os.path.exists(image_url):
                        os.remove(image_url)
                    else:
                        dict_error = {"code": int(1), "msg": "image文件不存在！"}
                        return json.dumps(dict_error, ensure_ascii=False)
                    init_fea.extract_feature_enter()

                    feature_change = 1
                    with open('feature_change.txt', 'w+') as f:
                        f.write(str(feature_change))
                    code = delperson_tables(p_id)
                    if code == 0:
                        dict_success = {"data": {"p_id": "{}".format(p_id)}, "code": int(0), "msg": "success"}

                        return json.dumps(dict_success, ensure_ascii=False)
                    else:
                        dict_error = {"code": int(1), "msg": "删除失败请检查数据库是否连接！"}
                        return json.dumps(dict_error, ensure_ascii=False)
                else:
                    dict_error = {"code": int(1), "msg": "手机号码错误！"}
                    return json.dumps(dict_error, ensure_ascii=False)
            else:
                dict_error = {"code": int(1), "msg": "验证无效！"}
                return json.dumps(dict_error, ensure_ascii=False)
        else:
            dict_error = {"code": int(1), "msg": "只接受post请求！"}
            return json.dumps(dict_error, ensure_ascii=False)

@app.route('/face/setperson' , methods=['GET', 'POST'])#更新人脸信息不改手机号,可以改name，对图片替换特征值，如果改手机号选择先删除再增加
def setperson():
    new = 0
    if request.method == 'POST':
        a = request.get_data()
        dict1 = json.loads(a)
        if dict1["appid"] == "ZQKJ2018":
            if len(dict1["data"]["p_id"]) == 11:
                p_id = dict1["data"]["p_id"]
                results = getperson_tables(p_id)
                if results != 1:
                    if results == ():
                        dict_error = {"code": int(1), "msg": "未录入此人信息！"}
                        return json.dumps(dict_error, ensure_ascii=False)
                    else:
                        if dict1["data"]["name"]:
                            name = dict1["data"]["name"]
                            if dict1["data"]["image"]:
                                tag = ""
                                try:
                                    if dict1["data"]["tag"]:
                                        tag = dict1["data"]["tag"]
                                except:
                                    tag = ""
                                if tag == "":
                                    tag = None

                                image_url = dict1["data"]["image"]
                                save_url = urls(image_url)
                                image0 = save_url.split('.')[1]  # 分离得到后缀
                                fileout = "./user_pic/{}.{}".format(p_id, image0)  # 直接覆盖原来的图片

                                urllib.request.urlretrieve(image_url, fileout)

                                # image_first = "./user_pic/{}.bmp".format(p_id)
                                image1 = cv2.imread(fileout)
                                # image2 = cv2.imread(image_first)
                                # difference = cv2.subtract(image1, image2)
                                # result = not np.any(difference)  # if difference is all zeros it will return False

                                # if result is True:
                                # print("两张图片一样")
                                # image_change = 0
                                # else:
                                # image_change = 1
                                # os.remove(image_first)
                                # cv2.imwrite(image_first, image1)
                                # print("两张图片不一样")

                                # if image_change == 1:  # 图片不一样时替换特征值
                                init_fea.setimage(image1, p_id)

                                feature_change = 1
                                with open('feature_change.txt', 'w+') as f:
                                    f.write(str(feature_change))
                                # os.remove(fileout)
                                code = setperson_tables(p_id, name, save_url, tag)
                                if code == 0:

                                    dict_success = {"data": {"p_id": "{}".format(p_id)}, "code": int(0),
                                                    "msg": "success"}
                                    return json.dumps(dict_success, ensure_ascii=False)
                                else:
                                    dict_error = {"code": int(1), "msg": "更新失败请检查数据库是否连接！"}
                                    return json.dumps(dict_error, ensure_ascii=False)
                            else:
                                dict_error = {"code": int(1), "msg": "请给出image参数！"}
                                return json.dumps(dict_error, ensure_ascii=False)
                        else:
                            dict_error = {"code": int(1), "msg": "请给出name参数！"}
                            return json.dumps(dict_error, ensure_ascii=False)
                else:
                    dict_error = {"code": int(1), "msg": "获取失败请检查数据库是否连接！"}
                    return json.dumps(dict_error, ensure_ascii=False)

            else:
                dict_error = {"code": int(1), "msg": "手机号码错误！"}
                return json.dumps(dict_error, ensure_ascii=False)
        else:
            dict_error = {"code": int(1), "msg": "验证无效！"}
            return json.dumps(dict_error, ensure_ascii=False)
    else:
        dict_error = {"code":int(1),"msg":"只接受post请求！"}
        return json.dumps(dict_error, ensure_ascii=False)

@app.route('/face/getperson' , methods=['GET', 'POST'])#获取人脸信息
def getperson():
    if request.method == 'POST':
        a = request.get_data()
        dict1 = json.loads(a)
        if dict1["appid"] == "ZQKJ2018":
            if len(dict1["data"]["p_id"]) == 11:
                p_id = dict1["data"]["p_id"]
                results = getperson_tables(p_id)


                if results != 1:
                    if results == ():
                        dict_error = {"code": int(1), "msg": "未录入此人信息！"}
                        return json.dumps(dict_error, ensure_ascii=False)
                    else:
                        name = results[0][2]
                        image = results[0][3]
                        image_url = "http://pbkpbtmwz.bkt.clouddn.com/egs" + image
                        #print(image)
                        tag = results[0][4]

                        dict_success = {"data": {"p_id": "{}".format(p_id), "name": "{}".format(name), "image": image_url, "tag":tag}, "code": int(0), "msg": "success"}
                        return json.dumps(dict_success, ensure_ascii=False)

                else:
                    dict_error = {"code": int(1), "msg": "获取失败请检查数据库是否连接！"}
                    return json.dumps(dict_error, ensure_ascii=False)

            else:
                dict_error = {"code": int(1), "msg": "手机号码错误！"}
                return json.dumps(dict_error, ensure_ascii=False)
        else:
            dict_error = {"code": int(1), "msg": "验证无效！"}
            return json.dumps(dict_error, ensure_ascii=False)
    else:
        dict_error = {"code":int(1),"msg":"只接受post请求！"}
        return json.dumps(dict_error, ensure_ascii=False)

@app.route('/face/verify' , methods=['GET', 'POST'])#人脸识别信息
def verify():
    currentTime_img = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    if request.method == 'POST':
        a = request.get_data()
        dict1 = json.loads(a)
        if dict1["appid"] == "ZQKJ2018":
            if dict1["data"]["image"]:
                image_url = dict1["data"]["image"]
                #print(image_url)
                fileout = './card/verify.bmp' # 先保存在card下
                urllib.request.urlretrieve(image_url, fileout)
                img = cv2.imread(fileout)
                p_id_list, api_unknum = verify_img(img)
                if p_id_list == [] and api_unknum != 0:
                    dict_success = {"code": int(0), "msg": "success", "data": {"已知访客": 0,
                                                                          "未知访客": "{}".format(api_unknum)}}
                    return json.dumps(dict_success, ensure_ascii=False)
                else:
                    result = []
                    facenum = len(p_id_list)
                    for p_id in p_id_list:
                        re = getperson_tables(p_id)
                        if re == 1:
                            result = 1
                        else:
                            # print(re)
                            re = re[0]
                            result.append(re)
                    if result == 1:
                        dict_error = {"code": int(1), "msg": "获取失败请检查数据库是否连接！"}
                        return json.dumps(dict_error, ensure_ascii=False)
                    else:

                        dict_success = {}
                        dict_success["code"] = int(0)
                        dict_success["msg"] = "success"
                        dict_success["data"] = {}
                        for i in range(facenum):
                            p_id = result[i][1]
                            name = result[i][2]
                            image = result[i][3]
                            # dict_success["person_{}".format(i)] = {"p_id": "{}".format(p_id), "name": "{}".format(name),
                            #                       "image": "{}".format(image)}
                            #image = "http://" + host_ip + ":5000" + "/user_pic/{}".format(p_id)
                            image_url = "http://pbkpbtmwz.bkt.clouddn.com/egs" + image
                            dict_success["data"]["person_{}".format(i)] = {"p_id": "{}".format(p_id),
                                                                           "name": "{}".format(name),
                                                                           "image": image_url}

                        dict_success["data"]["unknown"] = {"未知访客": "{}".format(api_unknum)}

                        return json.dumps(dict_success, ensure_ascii=False)



            else:
                 dict_error = {"code": int(1), "msg": "请给出image参数！"}
                 return json.dumps(dict_error, ensure_ascii=False)
        else:
            dict_error = {"code": int(1), "msg": "验证无效！"}
            return json.dumps(dict_error, ensure_ascii=False)
    else:
         dict_error = {"code": int(1), "msg": "只接受post请求！"}
         return json.dumps(dict_error, ensure_ascii=False)

#获取人数信息,如果当前时间没有记录则返回None,传过来的时间格式：%Y-%m-%d %H:%M:%S
@app.route('/face/count' , methods=['GET', 'POST'])
def count():
    if request.method == 'POST':
        a = request.get_data()
        dict1 = json.loads(a)
        if dict1["appid"] == "ZQKJ2018":
            #max_time, min_time = select_tables()
            begintime = dict1["data"]["begintime"]
            begintime= datetime.strptime(begintime, "%Y-%m-%d %H:%M:%S")
            endtime = dict1["data"]["endtime"]
            endtime = datetime.strptime(endtime, "%Y-%m-%d %H:%M:%S")

            count = select_count(begintime, endtime)
            if count != 1:
                dict_success = {"code": int(0), "msg": "success", "data": {"count": "{}".format(count)}}
                return json.dumps(dict_success, ensure_ascii=False)
            else:
                dict_error = {"code": int(1), "msg": "获取失败请检查数据库是否连接！"}
                return json.dumps(dict_error, ensure_ascii=False)

        else:
            dict_error = {"code": int(1), "msg": "验证无效！"}
            return json.dumps(dict_error, ensure_ascii=False)
    else:
        dict_error = {"code":int(1),"msg":"只接受post请求！"}
        return json.dumps(dict_error, ensure_ascii=False)






if __name__ == "__main__":

        dbname = 'face_info'
        #create_tables(dbname)
        #create_tables_url(dbname)
        #getperson_tables("13800000000")
       #` newperson_tables("18392886034", "陈二", "/user_pic/13800000002.bmp", )
        #newperson_tables("13800000000", "陈二", "/user_pic/13800000000.bmp", )
        #result=getperson_tables("13800000000")

       # select_count("2018-07-02 22:15:00","2018-07-02 22:22:20")
        #delperson_tables("12345678900")
        #setperson_tables( "13800000000","lijing", "/user_pic/13800000000")
        app.run(host = '0.0.0.0' , debug = 'True')



