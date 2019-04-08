# -*- coding: utf-8 -*-
# Form implementation generated from reading ui file 'face_verification_2018_5_10.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# 摄像头人脸识别，识别未知和已知访客，并保存当前捕捉到的人脸图片（保存在image_save)
# 每天人数统计：同一个人在当天多次进入作为一次（如果机器重启，当前已经统计的会被保存）
# 海康摄像头：79行和89行改配置
# 不重启情况下人员信息更新时第二天才会起效（在today_clean中有search_train）
# WARNING! All changes made in this file will be lost!


import cv2,sys,os,time
import math
import shutil
import time
import subprocess
import numpy as np
from multiprocessing import Process, Queue # 多进程
from PyQt4 import QtCore, QtGui
from feature_extractor2 import Extractor,NaiveDlib
from preprocess.crop_util import crop_rotate_v2
from preprocess.crop_util_search import crop_rotate_part
from preprocess.image_preprocess import proc_img
from collections import deque
from xlwt import *  #数据导出到表格需要使用
from search_engine import Search_engin
from config import *
from datetime import datetime , timedelta
import wmi
import hashlib
import pickle as pkl
from scipy import spatial
import dlib



try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


#定义的全局变量

License = ""
VIDEO_IMAGE = Queue()#放从摄像头读到的帧用于display_probe_image
probe_image = Queue()#放从display_probe_image保存的帧用于verify

def camera_reader(queue):
    video_capture = cv2.VideoCapture(0)#调试海康时换成HKcam
    count = 0
    while True:
        ret, image = video_capture.read()
        count = count+1
        #print (count)
        if ret:
            if count % 1 == 0:
                queue.put(image)
        else:
            video_capture = cv2.VideoCapture(0)#调试海康时换成HKcam

class Ui_license(object):                                      #验证授权码界面
    def setupUi(self, license):
        license.setObjectName(_fromUtf8("license"))
        license.resize(484, 230)
        self.label = QtGui.QLabel(license)
        self.label.setGeometry(QtCore.QRect(30, 40, 71, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("微软雅黑"))
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(license)
        self.label_2.setGeometry(QtCore.QRect(30, 100, 71, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("微软雅黑"))
        font.setPointSize(16)
        self.label_2.setFont(font)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.pushButton = QtGui.QPushButton(license)
        self.pushButton.setGeometry(QtCore.QRect(180, 180, 131, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("微软雅黑"))
        font.setPointSize(16)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.lineEdit = QtGui.QLineEdit(license)
        self.lineEdit.setGeometry(QtCore.QRect(120, 40, 341, 31))
        self.lineEdit.setReadOnly(True)
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.lineEdit_2 = QtGui.QLineEdit(license)
        self.lineEdit_2.setGeometry(QtCore.QRect(120, 100, 341, 31))
        self.lineEdit_2.setObjectName(_fromUtf8("lineEdit_2"))
        self.label_tip = QtGui.QLabel(license)
        self.label_tip.setGeometry(QtCore.QRect(140, 150, 211, 20))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("微软雅黑"))
        font.setPointSize(12)
        font.setUnderline(True)

        # pa = QtGui.QPalette()
        # pa.setColor(QtGui.QPalette.WindowText, QtGui.qRed)

        # self.label_tip.setPalette(pa)
        self.label_tip.alignment()

        self.label_tip.setFont(font)
        self.label_tip.setText(_fromUtf8(""))
        self.label_tip.setObjectName(_fromUtf8("label_tip"))
        self.lineEdit_2.setObjectName(_fromUtf8("lineEdit_2"))

        self.retranslateUi(license)
        QtCore.QMetaObject.connectSlotsByName(license)

    def retranslateUi(self, license):
        license.setWindowTitle(_translate("license", "Licese", None))
        self.label.setText(_translate("license", "机器码", None))
        self.label_2.setText(_translate("license", "授权码", None))
        self.pushButton.setText(_translate("license", "验证授权", None))
        w = wmi.WMI()
        for processor in w.Win32_Processor():
            # print ("Processor ID:",processor.ProcessorId.strip())
            self.lineEdit.setText(processor.ProcessorId.strip())
        self.pushButton.clicked.connect(self.examine_Clicked)
    def examine_Clicked(self):
        global isCheck
        global License

        LicenseLocal = self.lineEdit_2.text()
        if License == LicenseLocal:
            # qtm = QtGui.QMessageBox
            # msg_box = qtm(qtm.Warning, u"提示", u"认证通过！关闭本界面进入主界面！", qtm.Yes)  ##消息提示框
            # msg_box.exec_()
            self.label_tip.setText("认证通过，关闭后进入系统！")
            fp = open("driver.dat",'w')
            fp.write(License)
            fp.close()
            isCheck = True
            # self.close()
            # self.exit()
            # self.quit()
            # self.exec_()
        else:
            # qtm = QtGui.QMessageBox
            # msg_box = qtm(qtm.Warning, u"提示", u"授权码无效！", qtm.Yes)  ##消息提示框
            # msg_box.exec_()
            self.label_tip.setText(" 授权码无效，请重新输入！")
            self.isCheck = False



class Ui_Face_Verification(object):     #主界面
    def __init__(self):
        ext_model_path = './model/facenet/inception-ring-1024.pb'
        #self.video_capture = cv2.VideoCapture(camera_Id)
        #self.video_capture = cv2.VideoCapture(HKcam)
        self.is_camera_on = True
        self.id_image = None
        self.id_image2 = None
        self.id_image1_2 = None
        self.probe_image = None
        self.ID_label = 0
        self.count = 0
        self.ID_lib = {}
        self.ID_name = {}
        self.feature_data = None
        self.index_dict = None
        self.unknownum = 0  #当天未知人员总数
        self.knownum = 0



        #self.unknownfeature = np.asarray([]) #当天保存的未知访客的特征
        self.datetime = datetime.now().strftime('%Y_%m_%d')
        self.unknown_feature_read()


        #self.persontime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.naivedlib = NaiveDlib()
        self.extractor = Extractor(ext_model_path, gpu_fraction=0)#gpu_fraction显存占用比例
        temp = np.ones((5, 112, 96, 1))
        self.extractor.extract_feature(im_arr=temp)
        self.query = deque(maxlen=2)

        self.search_train()
        self.start()
        self.start_verify()



    def setupUi(self, Face_Verification):
        Face_Verification.setObjectName(_fromUtf8("Face_Verification"))
        # Face_Verification.setEnabled(True)
        # Face_Verification.resize(1301, 810)
        Face_Verification.setFixedSize(1300, 810)  # 界面固定大小
        Face_Verification.setStyleSheet(_fromUtf8("background-color: rgb(240, 248, 255);"))  # 界面背景色
        # Face_Verification.setStyleSheet(_fromUtf8("background-color: rgb(255, 222, 173);"))
        self.centralwidget = QtGui.QWidget(Face_Verification)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))

        self.horizontalLayoutWidget = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(20, 40, 131, 161))
        self.horizontalLayoutWidget.setObjectName(_fromUtf8("horizontalLayoutWidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.ID_photo1 = QtGui.QLabel(self.horizontalLayoutWidget)
        self.ID_photo1.setText(_fromUtf8(""))
        self.ID_photo1.setObjectName(_fromUtf8("ID_photo1"))
        self.ID_photo1.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout.addWidget(self.ID_photo1)

        self.horizontalLayoutWidget_13 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_13.setGeometry(QtCore.QRect(1050, 10, 151, 151))
        self.horizontalLayoutWidget_13.setObjectName(_fromUtf8("horizontalLayoutWidget_13"))
        self.horizontalLayout_13 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_13)
        self.horizontalLayout_13.setObjectName(_fromUtf8("horizontalLayout_13"))
        self.logo = QtGui.QLabel(self.horizontalLayoutWidget_13)
        self.logo.setText(_fromUtf8(""))
        self.logo.setObjectName(_fromUtf8("logo"))
        self.logo.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_13.addWidget(self.logo)

        self.horizontalLayoutWidget_2 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(160, 40, 131, 161))
        self.horizontalLayoutWidget_2.setObjectName(_fromUtf8("horizontalLayoutWidget_2"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.ID_photo2 = QtGui.QLabel(self.horizontalLayoutWidget_2)
        self.ID_photo2.setText(_fromUtf8(""))
        self.ID_photo2.setObjectName(_fromUtf8("ID_photo2"))
        self.ID_photo2.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_2.addWidget(self.ID_photo2)

        self.horizontalLayoutWidget_3 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_3.setGeometry(QtCore.QRect(300, 40, 131, 161))
        self.horizontalLayoutWidget_3.setObjectName(_fromUtf8("horizontalLayoutWidget_3"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_3)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.ID_photo3 = QtGui.QLabel(self.horizontalLayoutWidget_3)
        self.ID_photo3.setText(_fromUtf8(""))
        self.ID_photo3.setObjectName(_fromUtf8("ID_photo3"))
        self.ID_photo3.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_3.addWidget(self.ID_photo3)
        self.horizontalLayoutWidget_4 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_4.setGeometry(QtCore.QRect(20, 210, 131, 161))
        self.horizontalLayoutWidget_4.setObjectName(_fromUtf8("horizontalLayoutWidget_4"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_4)
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.ID_photo4 = QtGui.QLabel(self.horizontalLayoutWidget_4)
        self.ID_photo4.setText(_fromUtf8(""))
        self.ID_photo4.setObjectName(_fromUtf8("ID_photo4"))
        self.ID_photo4.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_4.addWidget(self.ID_photo4)
        self.horizontalLayoutWidget_5 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_5.setGeometry(QtCore.QRect(160, 210, 131, 161))
        self.horizontalLayoutWidget_5.setObjectName(_fromUtf8("horizontalLayoutWidget_5"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_5)
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.ID_photo5 = QtGui.QLabel(self.horizontalLayoutWidget_5)
        self.ID_photo5.setText(_fromUtf8(""))
        self.ID_photo5.setObjectName(_fromUtf8("ID_photo5"))
        self.ID_photo5.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_5.addWidget(self.ID_photo5)
        self.horizontalLayoutWidget_6 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_6.setGeometry(QtCore.QRect(300, 210, 131, 161))
        self.horizontalLayoutWidget_6.setObjectName(_fromUtf8("horizontalLayoutWidget_6"))
        self.horizontalLayout_6 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_6)
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.ID_photo6 = QtGui.QLabel(self.horizontalLayoutWidget_6)
        self.ID_photo6.setText(_fromUtf8(""))
        self.ID_photo6.setObjectName(_fromUtf8("ID_photo6"))
        self.ID_photo6.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_6.addWidget(self.ID_photo6)
        self.verticalLayoutWidget = QtGui.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(560, 170, 681, 551))
        self.verticalLayoutWidget.setObjectName(_fromUtf8("verticalLayoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.Probe_photo = QtGui.QLabel(self.verticalLayoutWidget)
        self.Probe_photo.setText(_fromUtf8(""))
        self.Probe_photo.setObjectName(_fromUtf8("Probe_photo"))
        self.Probe_photo.setAlignment(QtCore.Qt.AlignCenter)
        self.verticalLayout.addWidget(self.Probe_photo)
        self.horizontalLayoutWidget_7 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_7.setGeometry(QtCore.QRect(20, 410, 131, 161))
        self.horizontalLayoutWidget_7.setObjectName(_fromUtf8("horizontalLayoutWidget_7"))
        self.horizontalLayout_7 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_7)
        self.horizontalLayout_7.setObjectName(_fromUtf8("horizontalLayout_7"))
        self.ID_photo1_2 = QtGui.QLabel(self.horizontalLayoutWidget_7)  # 未知照片
        self.ID_photo1_2.setText(_fromUtf8(""))
        self.ID_photo1_2.setObjectName(_fromUtf8("ID_photo1_2"))
        self.ID_photo1_2.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_7.addWidget(self.ID_photo1_2)
        self.horizontalLayoutWidget_8 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_8.setGeometry(QtCore.QRect(160, 410, 131, 161))
        self.horizontalLayoutWidget_8.setObjectName(_fromUtf8("horizontalLayoutWidget_8"))
        self.horizontalLayout_8 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_8)
        self.horizontalLayout_8.setObjectName(_fromUtf8("horizontalLayout_8"))
        self.ID_photo1_3 = QtGui.QLabel(self.horizontalLayoutWidget_8)
        self.ID_photo1_3.setText(_fromUtf8(""))
        self.ID_photo1_3.setObjectName(_fromUtf8("ID_photo1_3"))
        self.ID_photo1_3.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_8.addWidget(self.ID_photo1_3)
        self.horizontalLayoutWidget_9 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_9.setGeometry(QtCore.QRect(300, 410, 131, 161))
        self.horizontalLayoutWidget_9.setObjectName(_fromUtf8("horizontalLayoutWidget_9"))
        self.horizontalLayout_9 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_9)
        self.horizontalLayout_9.setObjectName(_fromUtf8("horizontalLayout_9"))
        self.ID_photo1_4 = QtGui.QLabel(self.horizontalLayoutWidget_9)
        self.ID_photo1_4.setText(_fromUtf8(""))
        self.ID_photo1_4.setObjectName(_fromUtf8("ID_photo1_4"))
        self.ID_photo1_4.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_9.addWidget(self.ID_photo1_4)
        self.horizontalLayoutWidget_10 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_10.setGeometry(QtCore.QRect(20, 580, 131, 161))
        self.horizontalLayoutWidget_10.setObjectName(_fromUtf8("horizontalLayoutWidget_10"))
        self.horizontalLayout_10 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_10)
        self.horizontalLayout_10.setObjectName(_fromUtf8("horizontalLayout_10"))
        self.ID_photo1_5 = QtGui.QLabel(self.horizontalLayoutWidget_10)
        self.ID_photo1_5.setText(_fromUtf8(""))
        self.ID_photo1_5.setObjectName(_fromUtf8("ID_photo1_5"))
        self.ID_photo1_5.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_10.addWidget(self.ID_photo1_5)
        self.horizontalLayoutWidget_11 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_11.setGeometry(QtCore.QRect(160, 580, 131, 161))
        self.horizontalLayoutWidget_11.setObjectName(_fromUtf8("horizontalLayoutWidget_11"))
        self.horizontalLayout_11 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_11)
        self.horizontalLayout_11.setObjectName(_fromUtf8("horizontalLayout_11"))
        self.ID_photo1_6 = QtGui.QLabel(self.horizontalLayoutWidget_11)
        self.ID_photo1_6.setText(_fromUtf8(""))
        self.ID_photo1_6.setObjectName(_fromUtf8("ID_photo1_6"))
        self.ID_photo1_6.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_11.addWidget(self.ID_photo1_6)
        self.horizontalLayoutWidget_12 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_12.setGeometry(QtCore.QRect(300, 580, 131, 161))
        self.horizontalLayoutWidget_12.setObjectName(_fromUtf8("horizontalLayoutWidget_12"))
        self.horizontalLayout_12 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_12)
        self.horizontalLayout_12.setObjectName(_fromUtf8("horizontalLayout_12"))
        self.ID_photo1_7 = QtGui.QLabel(self.horizontalLayoutWidget_12)
        self.ID_photo1_7.setText(_fromUtf8(""))
        self.ID_photo1_7.setObjectName(_fromUtf8("ID_photo1_7"))
        self.ID_photo1_7.setAlignment(QtCore.Qt.AlignCenter)
        self.horizontalLayout_12.addWidget(self.ID_photo1_7)
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(20, 10, 111, 21))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("微软雅黑"))
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(30, 380, 111, 21))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("微软雅黑"))
        font.setPointSize(10)
        self.label_2.setFont(font)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_3 = QtGui.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(760, 60, 261, 81))

        font = QtGui.QFont()
        font.setFamily(_fromUtf8("微软雅黑"))
        font.setBold(1)
        font.setPointSize(24)

        self.label_3.setFont(font)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        Face_Verification.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(Face_Verification)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1366, 23))
        self.menubar.setObjectName(_fromUtf8("menubar"))

        self.menu = QtGui.QMenu(self.menubar)
        self.menu.setObjectName(_fromUtf8("menu"))

        self.menu2 = QtGui.QMenu(self.menubar)
        self.menu2.setObjectName(_fromUtf8("menu2"))

        Face_Verification.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(Face_Verification)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        Face_Verification.setStatusBar(self.statusbar)
        self.action_check = QtGui.QAction(Face_Verification)
        self.action_check.setObjectName(_fromUtf8("action_check"))
        self.action_thresh = QtGui.QAction(Face_Verification)
        self.action_thresh.setObjectName(_fromUtf8("action_thresh"))
        self.action_camera_on = QtGui.QAction(Face_Verification)
        self.action_camera_on.setObjectName(_fromUtf8("action_camera_on"))
        self.action_camera_off = QtGui.QAction(Face_Verification)
        self.action_camera_off.setObjectName(_fromUtf8("action_camera_off"))

        self.menu.addAction(self.action_check)
        self.menu.addAction(self.action_thresh)
        self.menubar.addAction(self.menu.menuAction())

        self.menu2.addAction(self.action_camera_on)
        self.menu2.addAction(self.action_camera_off)
        self.menubar.addAction(self.menu2.menuAction())

        self.retranslateUi(Face_Verification)
        QtCore.QMetaObject.connectSlotsByName(Face_Verification)

    def retranslateUi(self, Face_Verification):

        # _translate = QtCore.QCoreApplication.translate
        Face_Verification.setWindowTitle(_translate("Face_Verification", "智擎信息系统（上海）有限公司", None))
       # Face_Verification.setWindowTitle(_translate("Face_Verification", "MainWindow", None))
        self.label.setText("已登记访客")
        self.label_2.setText("未知访客")
        #self.label_3.setText("智擎信息系统")
        self.label_3.setText(_translate("Face_Verification",
                                        "<html><head/><body><p align=\"center\"><span style=\" font-size:24pt;\">智擎信息系统</span></p></body></html>",
                                        None))
        #self.menu.setTitle(_translate("Face_Verification", "信息查询", None))
        #self.menu2.setTitle(_translate("Face_Verification", "访客登记", None))
        #self.action_known.setText(_translate("Face_Verification", "已知访客", None))
        #self.action_unknown.setText(_translate("Face_Verification", "未知访客", None))

        self.menu.setTitle("系统管理")
        self.action_check.setText("信息查询")
        self.action_check.setToolTip("信息查询")
        self.action_thresh.setText("阈值设定")

        self.menu2.setTitle("摄像头管理")
        self.action_camera_on.setText("开摄像头")
        self.action_camera_off.setText("关摄像头")

        pixMap1 = QtGui.QPixmap("ID_test.jpg")
        self.ID_photo1.setScaledContents(True)
        self.ID_photo2.setScaledContents(True)
        self.ID_photo1.setPixmap(pixMap1)
        self.ID_photo1_2.setScaledContents(True)
        self.ID_photo1_3.setScaledContents(True)
        self.ID_photo1_4.setScaledContents(True)
        self.ID_photo1_5.setScaledContents(True)
        self.ID_photo1_6.setScaledContents(True)
        self.ID_photo1_7.setScaledContents(True)
        self.ID_photo3.setScaledContents(True)
        self.ID_photo4.setScaledContents(True)
        self.ID_photo5.setScaledContents(True)
        self.ID_photo6.setScaledContents(True)
        pixmap2 = QtGui.QPixmap("logo.png")
        self.logo.setScaledContents(True)
        self.logo.setPixmap(pixmap2)


    def display_id_image(self, i):# 显示已知访客照片，一次最多显示六张
        image = cv2.cvtColor(self.id_image, cv2.COLOR_BGR2RGB)
        image = QtGui.QImage(image, image.shape[1],\
                            image.shape[0], image.shape[1] * 3,QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap(image)
        i = int(i % 6)
        if i == 0:
            self.ID_photo1.setPixmap(pix)
        if i == 1:
            self.ID_photo2.setPixmap(pix)
        if i == 2:
            self.ID_photo3.setPixmap(pix)
        if i == 3:
            self.ID_photo4.setPixmap(pix)
        if i == 4:
            self.ID_photo5.setPixmap(pix)
        if i == 5:
            self.ID_photo6.setPixmap(pix)

    def display_id_image2(self, i):  # 显示未知访客照片，一次最多显示六张

        image = cv2.cvtColor(self.id_image2, cv2.COLOR_BGR2RGB)
        image = QtGui.QImage(image, image.shape[1],\
                            image.shape[0], image.shape[1] * 3,QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap(image)
        i = int(i % 6)
        if i == 0:
            self.ID_photo1_2.setPixmap(pix)
        if i == 1:
            self.ID_photo1_3.setPixmap(pix)
        if i == 2:
            self.ID_photo1_4.setPixmap(pix)
        if i == 3:
            self.ID_photo1_5.setPixmap(pix)
        if i == 4:
            self.ID_photo1_6.setPixmap(pix)
        if i == 5:
            self.ID_photo1_7.setPixmap(pix)

    def search_train(self):#已知访客搜索初始化 后面补充一个一天的清空时加入这个为了人员信息管理时的更新
        with open('./data/index_enter.pkl', 'rb') as f:
            self.index_dict = pkl.load(f)
        with open('./data/database_enter.npy', 'rb') as f:
            self.feature_data = np.load('./data/database_enter.npy')
        self.search_eign = Search_engin(self.feature_data)
        self.search_eign.train()

    def unknown_feature_read(self):#重启后当天的数据仍然保存（已知访客人数也在这里保存）
        self.datetime = datetime.now().strftime('%Y_%m_%d')
        self.unknownfeature_path = './data/unknown_feature.npy'
        self.unknown_pic_path = './image_saved/{}/unknown'.format(self.datetime)
        self.known_pic_path = './image_saved/{}/known'.format(self.datetime)
        if os.path.exists(self.unknownfeature_path) and os.path.exists(self.unknown_pic_path):
            try:
                self.unknownfeature = np.load(self.unknownfeature_path)
                self.unknownum = len(os.listdir(self.unknown_pic_path))
            except:
                self.unknownfeature = np.asarray([])

        else:
            self.unknownfeature = np.asarray([])
            self.unknownum = 0
        if os.path.exists(self.known_pic_path):
            self.knownum = len(os.listdir(self.known_pic_path))
        else:
            self.knownum = 0

     #当天数据清除和人数保存
    def today_clean(self, datetime): #旧日期
        number = self.unknownum + self.knownum
        with open('./image_saved/{}/number.txt'.format(datetime), 'w+') as f:
            f.write(str(number))
        if os.path.exists(self.unknownfeature_path):
            os.remove(self.unknownfeature_path)
        self.search_train()
        self.knownum = 0
        self.unknownum = 0
        self.unknownfeature = np.asarray([])

    # 识别比对
    def verify(self, thresh):
        global VIDEO_IMAGE
        global isPass
        knownflag = 0
        unknownflag = 0
        currentunknownum = 0
        currentknownum = 0
        idname = []  # 可显示id照片的编号列表
        currentDate = datetime.now().strftime('%Y_%m_%d')
        currentTime = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        if currentDate != self.datetime: #新日期触发
            self.today_clean(self.datetime)
            self.datetime = currentDate
        web = Web_Browser()
        web.setModal(False)
        web.setWindowTitle(_translate("Face_Verification", "比对结果", None))
        # if self.pic_time != None and (datetime.datetime.now() - self.pic_time).seconds > pic_time:
            # self.image_clear()

        for i in range(probe_image.qsize()):
            image1 = probe_image.get()
        #image1 = cv2.imread('./card/2.jpg')  # 加载图片测试
        if image1 is not None:
            print('get image')
            image1 = cv2.flip(image1, 1)
            width = int(image1.shape[1] / 2)
            height = int(image1.shape[0] / 2)
            image = cv2.resize(image1.copy(), (width, height))

            try:
                    #total_start = time.time()
                    bboxs = self.naivedlib.getALLFaces(image)
                    #bbox_end = time.time()
                    print('bbox detect took ')
                    bboxs = [dlib.rectangle(int(bbox.left() * downsample_ratio), int(bbox.top() * downsample_ratio),
                                            int(bbox.right() * downsample_ratio), int(bbox.bottom() * downsample_ratio))
                             for bbox in bboxs]
                    facenum = len(bboxs)

                    #print(facenum)#人脸数
                    # index_list = []
                    #idname = []  # 可显示id照片的编号列表
                    if bboxs is not None:
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
                            print(name_list)
                            print(score_list)
                            #person_list = [name.split('_')[0] for name in name_list]
                            #person_set = list(set(person_list))
                            #person_num = len(person_set)
                            #print(person_num)

                            score = 1 - spatial.distance.cosine(feature, self.feature_data[int(idx_list[0])])
                            thresh = float(thresh)
                            print(thresh)
                            if score > thresh:
                                knownflag = 1
                                name = name_list[0]
                                if self.knownum == 0:
                                    self.knownum = 1
                                    if not os.path.exists('./image_saved/{}'.format(currentDate)):
                                        os.mkdir('./image_saved/{}'.format(currentDate))
                                        os.mkdir('./image_saved/{}/unknown'.format(currentDate))
                                        os.mkdir('./image_saved/{}/known'.format(currentDate))
                                    cv2.imwrite('./image_saved/{}/known/{}_{}.jpg'.format(currentDate, currentTime,
                                                                                            name),
                                                save_croped)
                                    idname.append(name) #当前帧中的已知访客name
                                    print("欢迎" + name)
                                    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                                else:
                                    img_list = os.listdir(self.known_pic_path)  # 返回指定的文件夹包含的文件或文件夹的名字的列表
                                    knownlist = [item.split('.')[0] for item in img_list]
                                    knownlist = [item.split('_')[1] for item in knownlist]
                                    if name not in knownlist:
                                        cv2.imwrite('./image_saved/{}/known/{}_{}.jpg'.format(currentDate, currentTime,
                                                                                            name),
                                                save_croped)
                                        idname.append(name) #当前帧中的已知访客name
                                        self.knownum = self.knownum + 1
                                        print("欢迎" + name)
                                        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

                            else:
                                unknownflag = 1
                                if self.unknownum == 0:
                                    print("第一个未知人员")
                                    currentunknownum = currentunknownum + 1
                                    self.unknownum = 1
                                    #self.unknownlist[self.unknownum] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    if not os.path.exists('./image_saved/{}'.format(currentDate)):
                                        os.mkdir('./image_saved/{}'.format(currentDate))
                                        os.mkdir('./image_saved/{}/unknown'.format(currentDate))
                                        os.mkdir('./image_saved/{}/known'.format(currentDate))

                                    cv2.imwrite('./image_saved/{}/unknown/{}_{}.jpg'.format(currentDate, currentTime,
                                                                                        self.unknownum),save_croped)
                                    self.unknownfeature = feature[np.newaxis, :]

                                else:
                                    unthresh = 0.6
                                    self.search_eign_unknown = Search_engin(self.unknownfeature)  # 未知访客搜索
                                    self.search_eign_unknown.train()
                                    unknown_idx = self.search_eign_unknown.search(feature)
                                    unknown_idx = [unknown_idx[0][i] for i in range(unknown_idx.shape[1])]
                                    print(unknown_idx)
                                    uscore = 1 - spatial.distance.cosine(feature, self.unknownfeature[int(unknown_idx[0])])
                                    print(uscore)
                                    if uscore < unthresh: # 当天第一次识别出该未知人员
                                        self.unknownum = self.unknownum + 1
                                        currentunknownum = currentunknownum + 1
                                        #self.unknownlist[self.unknownum] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        cv2.imwrite('./image_saved/{}/unknown/{}_{}.jpg'.format(currentDate, currentTime,
                                                                                    self.unknownum), save_croped)
                                        self.unknownfeature = np.vstack((self.unknownfeature, feature))
                                        #print("第二个")
                                        #print(time.strftime('%H:%M:%S', time.localtime(time.time())))

                        if knownflag == 1:
                            #print(idname)
                            currentknownum = len(idname)  # 当前帧已知访客数量
                            #self.knownum = self.knownum + currentknownum
                            for i in range(currentknownum):
                                self.id_image = cv2.imread('./user_pic/{}.bmp'.format(idname[i]))
                                self.display_id_image(self.knownum)
                        if unknownflag == 1:
                            print("未知人总数:{}".format(self.unknownum))
                           # print("当前帧未知人数:{}".format(currentunknownum))
                            with open(self.unknownfeature_path, 'wb') as f:
                                self.unknownfeature = np.asarray(self.unknownfeature)
                                np.save(f, self.unknownfeature)
                            for i in range(currentunknownum):
                                self.id_image2 = cv2.imread('./image_saved/{}/unknown/{}_{}.jpg'.format(currentDate, currentTime, self.unknownum))
                                self.display_id_image2(self.unknownum)

                        #print(time.strftime('%H:%M:%S', time.localtime(time.time())))
                    else:

                        web.write_result("未检测到人脸", 'red')
                        web.exec_()

            except:
                    pass
        else:
            pass

    def display_probe_image(self):

        #ret, image1 = self.video_capture.read()
        if VIDEO_IMAGE.qsize() != 0:
            for i in range(VIDEO_IMAGE.qsize()):
                image1 = VIDEO_IMAGE.get()
                probe_image.put(image1)
            self.probe_image = image1.copy()

            try:
                #bbox = self.naivedlib.getLargestFaceBoundingBox(image1)
                bboxs = self.naivedlib.getALLFaces(image1)
                image1 = self.naivedlib.drawbboxs(image1, bboxs)

            except:
                pass
            image = cv2.cvtColor(image1, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, (320 * 2, 240 * 2))
            # image = cv2.flip(image,1)
            image = QtGui.QImage(image, image.shape[1], \
                                 image.shape[0], image.shape[1] * 3, QtGui.QImage.Format_RGB888)
            pix = QtGui.QPixmap.fromImage(image)
            self.Probe_photo.setPixmap(pix)
        else:
            self.probe_image = None
            self.Probe_photo.setText(_translate("Face_Verification", "未读取到图片", None))
            self.Probe_photo.setStyleSheet('color: red')


    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.display_probe_image)

        self.timer.start(1000./24)


    def start_verify(self):
        self.timer3= QtCore.QTimer()
        global thresh
        self.timer3.timeout.connect(lambda: self.verify(thresh))
        self.timer3.start(1000)#1000ms==1s进行一次识别




class Web_Browser(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self)
        self.setObjectName(_fromUtf8("Result"))
        Web_Browser.setStyleSheet(self,_fromUtf8("background-color: rgb(240, 248, 255);"))  # 界面背景色
        self.resize(400, 102)
        self.verticalLayoutWidget = QtGui.QWidget(self)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(40, 10, 301, 80))
        self.verticalLayoutWidget.setObjectName(_fromUtf8("verticalLayoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(18)
        self.label.setFont(font)
        self.label.setText(_fromUtf8(""))
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)


    def write_result(self,string,color='green'):
        self.label.setText(_translate("Result",string, None))
        self.label.setStyleSheet('color: {}'.format(color))
        QtCore.QTimer.singleShot(2000,self.close)         #弹出框停留时间2秒



def code():
    global License
    w = wmi.WMI()
    for processor in w.Win32_Processor():
        CPUID = processor.ProcessorId.strip()
    m = hashlib.md5()
    m.update(CPUID.encode("utf8"))
    License = m.hexdigest()
    temp = []
    for i in range(len(CPUID)):
        temp.append(License[i])
        temp.append(CPUID[i])
    License = ''.join(temp)
    print(License)




if __name__ == "__main__":
    code()            #授权码
    app = QtGui.QApplication(sys.argv)


    if os.path.exists("driver.dat"):
        fp = open("driver.dat", 'r')  # 直接以读写模式打开一个文件，如果文件不存在则创建文件
        stri = fp.read()  # 读一行，如果定义了size，有可能返回的只是一行的一部分
        # print(stri)
        fp.close()
    else:
        fp = open("driver.dat", 'a+')  # 直接以读写模式打开一个文件，如果文件不存在则创建文件
        stri = fp.read()  # 读一行，如果定义了size，有可能返回的只是一行的一部分
        # print(stri)
        fp.close()

    if stri == License:
        #设置界面风格
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))  # Windows   WindowsXP   WindowsVista   Motif   CDE   Plastique   Cleanlooks
        # QtGui.QApplication.setPalette(QtGui.QApplication.style().standardPalette())    #设置成风格的标准颜色
        Face_Verification = QtGui.QMainWindow()
        p = Process(target=camera_reader, args=(VIDEO_IMAGE,))
        p.start()
        ui = Ui_Face_Verification()
        ui.setupUi(Face_Verification)
        Face_Verification.show()
    else:
        license = QtGui.QDialog()
        ui = Ui_license()
        ui.setupUi(license)
        license.show()
        # print(Ui_license.isCheck)
        license.exec()


    sys.exit(app.exec_())

