# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'work_try.ui'
#
# Created: Tue Jul 18 16:36:13 2017
#      by: PyQt4 UI code generator 4.10.4
#
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
import sqlite3      #导入数据库
from config import *
from datetime import datetime
import re
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
thresh = 0.55
Name = ''
sex = ''
nation = ''
BirDate = ''
Address = ''
CardID = ''
Authority = ''
Period = ''
currentDate = ''
isPass = ''
IDPhoto = ''
photo = ''

list = [[]]
count = 0   #统计数据数量

isCheck = False
License = ""
VIDEO_IMAGE = Queue()

def camera_reader(queue):
    video_capture = cv2.VideoCapture(0)
    count = 0
    while True:
        ret, image = video_capture.read()
        count = count+1
        # print (ret,image)
        if ret:
            queue.put(image)
            cv2.imshow('image', image)
            key = cv2.waitKey(1)

            if key & 0xFF == ord('q'):
                break
        else:
            video_capture = cv2.VideoCapture(0)

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


class Ui_threshold_setting(object):       #阈值修改界面
    def setupUi(self, threshold_setting):
        threshold_setting.setStyleSheet(_fromUtf8("background-color: rgb(240, 248, 255);"))  # 界面背景色
        threshold_setting.setObjectName(_fromUtf8("threshold_setting"))
        threshold_setting.setFixedSize(438, 220)
        self.label = QtGui.QLabel(threshold_setting)
        self.label.setGeometry(QtCore.QRect(90, 80, 71, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("黑体"))
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.edit_threshold = QtGui.QLineEdit(threshold_setting)
        self.edit_threshold.setGeometry(QtCore.QRect(240, 80, 113, 31))
        self.edit_threshold.setObjectName(_fromUtf8("edit_threshold"))
        self.label_hint = QtGui.QLabel(threshold_setting)
        self.label_hint.setGeometry(QtCore.QRect(180, 130, 91, 21))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("黑体"))
        font.setPointSize(12)
        self.label_hint.setFont(font)
        self.label_hint.setText(_fromUtf8(""))
        self.label_hint.setObjectName(_fromUtf8("label_hint"))
        self.set_button = QtGui.QPushButton(threshold_setting)
        self.set_button.setGeometry(QtCore.QRect(170, 160, 111, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("黑体"))
        font.setPointSize(12)
        self.set_button.setFont(font)
        self.set_button.setObjectName(_fromUtf8("set_button"))
        self.label_3 = QtGui.QLabel(threshold_setting)
        self.label_3.setGeometry(QtCore.QRect(90, 30, 71, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("黑体"))
        font.setPointSize(12)
        self.label_3.setFont(font)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.label_4 = QtGui.QLabel(threshold_setting)
        self.label_4.setGeometry(QtCore.QRect(250, 30, 71, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("黑体"))
        font.setPointSize(12)
        self.label_4.setFont(font)
        self.label_4.setObjectName(_fromUtf8("label_4"))

        self.retranslateUi(threshold_setting)
        QtCore.QMetaObject.connectSlotsByName(threshold_setting)

    def retranslateUi(self, threshold_setting):
        threshold_setting.setWindowTitle(_translate("threshold_setting", "Form", None))
        self.label.setText(_translate("threshold_setting", "新 阈 值", None))
        self.set_button.setText(_translate("threshold_setting", "设置", None))
        self.label_3.setText(_translate("threshold_setting", "当前阈值", None))
        self.label_4.setText(_translate("threshold_setting", str(thresh), None))      #显示的当前阈值随着设置的thresh更改而变化
        self.set_button.clicked.connect(self.threshold_setting_button_clickd)


    def threshold_setting_button_clickd(self):
        # thresh
        global thresh
        str = self.edit_threshold.text()

        temp = re.compile('^(0.[0-9]{1,5})?$')                      #正则匹配0-1的小数，可包含1-5位小数位

        if temp.match(str):         #判断是不是符合条件的小数
            thresh = float(str)
            self.label_4.setText(str)
            write_thresh()
            qtm = QtGui.QMessageBox
            msg_box = qtm(qtm.Warning, u"提示", u"设置成功！", qtm.Yes)  ##消息提示框
            msg_box.exec_()
        else:
            qtm = QtGui.QMessageBox
            msg_box = qtm(qtm.Warning, u"提示", u"请输入0.00-1.00的小数！", qtm.Yes)  ##消息提示框
            msg_box.exec_()


class Ui_ui_check(object):   #查询界面
    def setupUi(self, ui_check):
        ui_check.setStyleSheet(_fromUtf8("background-color: rgb(240, 248, 255);"))  # 界面背景色
        ui_check.setObjectName("ui_check")
        ui_check.setFixedSize(880, 545)
        self.edit_name = QtGui.QLineEdit(ui_check)
        self.edit_name.setGeometry(QtCore.QRect(20, 19, 121, 31))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.edit_name.setFont(font)
        self.edit_name.setObjectName("edit_name")
        self.name_check_button = QtGui.QPushButton(ui_check)
        self.name_check_button.setGeometry(QtCore.QRect(20, 60, 121, 31))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        self.name_check_button.setFont(font)
        self.name_check_button.setObjectName("name_check_button")
        self.edit_ID = QtGui.QLineEdit(ui_check)
        self.edit_ID.setGeometry(QtCore.QRect(170, 19, 121, 31))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.edit_ID.setFont(font)
        self.edit_ID.setObjectName("edit_ID")
        self.ID_check_button = QtGui.QPushButton(ui_check)
        self.ID_check_button.setGeometry(QtCore.QRect(170, 60, 121, 31))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        self.ID_check_button.setFont(font)
        self.ID_check_button.setObjectName("ID_check_button")
        self.time_check_button = QtGui.QPushButton(ui_check)
        self.time_check_button.setGeometry(QtCore.QRect(320, 61, 251, 31))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        self.time_check_button.setFont(font)
        self.time_check_button.setObjectName("time_check_button")

        self.unpassed_check_button = QtGui.QPushButton(ui_check)
        self.unpassed_check_button.setGeometry(QtCore.QRect(590, 61, 121, 31))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        self.unpassed_check_button.setFont(font)
        self.unpassed_check_button.setObjectName("unpassed_check_button")
        self.export_button = QtGui.QPushButton(ui_check)
        self.export_button.setGeometry(QtCore.QRect(740, 20, 121, 31))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        self.export_button.setFont(font)
        self.export_button.setObjectName("export_button")

        self.delete_button = QtGui.QPushButton(ui_check)
        self.delete_button.setGeometry(QtCore.QRect(740, 60, 121, 31))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        self.delete_button.setFont(font)
        self.delete_button.setObjectName("delete_button")

        Date = QtCore.QDateTime.currentDateTime()

        self.edit_time1 = QtGui.QDateEdit(ui_check)
        self.edit_time1.setDisplayFormat("yyyy-MM-dd")
        self.edit_time1.setDateTime(Date)
        self.edit_time1.setGeometry(QtCore.QRect(320, 20, 121, 31))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.edit_time1.setFont(font)
        self.edit_time1.setObjectName("edit_time1")

        self.edit_time2 = QtGui.QDateEdit(ui_check)
        self.edit_time2.setDisplayFormat("yyyy-MM-dd")
        self.edit_time2.setDateTime(Date)
        self.edit_time2.setGeometry(QtCore.QRect(450, 20, 121, 31))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        self.edit_time2.setFont(font)
        self.edit_time2.setObjectName("edit_time2")
        self.passed_check_button = QtGui.QPushButton(ui_check)
        self.passed_check_button.setGeometry(QtCore.QRect(590, 20, 121, 31))
        font = QtGui.QFont()
        font.setFamily("微软雅黑")
        font.setPointSize(12)
        self.passed_check_button.setFont(font)
        self.passed_check_button.setObjectName("passed_check_button")

        self.tableWidget = QtGui.QTableWidget(ui_check)
        self.tableWidget.setGeometry(QtCore.QRect(20, 100, 841, 431))
        self.tableWidget.setObjectName("tableWidget")

        self.tableWidget.setColumnCount(11)   #确定有多少行列
        # self.tableWidget.setRowCount(1000)
        self.tableWidget.horizontalHeader().setStretchLastSection(True);  #最后一栏自适应宽度
        self.tableWidget.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)   #先自适应宽度
        self.tableWidget.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)   #根据内容自动调整给定列宽
        self.tableWidget.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(3, QtGui.QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(4, QtGui.QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(5, QtGui.QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(6, QtGui.QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(7, QtGui.QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(8, QtGui.QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(9, QtGui.QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setResizeMode(10, QtGui.QHeaderView.ResizeToContents)

        self.tableWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)  # 整行选中的方式

        self.tableWidget.clearContents()
        self.tableWidget.setHorizontalHeaderLabels(['姓名', '性别','身份证号(ID)','读卡时间', '是否通过','民族', '生日','地址','签发机关','有效期','识别分数'])   #添加表头

        self.retranslateUi(ui_check)
        QtCore.QMetaObject.connectSlotsByName(ui_check)

    def retranslateUi(self, ui_check):
        _translate = QtCore.QCoreApplication.translate
        ui_check.setWindowTitle(_translate("ui_check", "Dialog"))
        self.name_check_button.setText("姓名查询")
        self.ID_check_button.setText("ID查询")
        self.time_check_button.setText("时间查询")
        self.unpassed_check_button.setText("验证未通过查询")
        self.export_button.setText("导出")
        self.delete_button.setText("删除")
        self.passed_check_button.setText("验证通过查询")
        self.tableWidget.setColumnCount(10)
        self.tableWidget.clearContents()

        self.name_check_button.clicked.connect(self.name_check_button_clicked)
        self.ID_check_button.clicked.connect(self.ID_check_button_clicked)
        self.time_check_button.clicked.connect(self.time_check_button_clicked)
        self.passed_check_button.clicked.connect(self.passed_check_button_clickd)
        self.unpassed_check_button.clicked.connect(self.unpassed_check_button_clicked)
        self.export_button.clicked.connect(self.export_button_clicked)
        self.delete_button.clicked.connect(self.delete_button_clicked)

        select()   #一进入查询页面，显示所有信息

        self.tableWidget_insert_data()

        #click消息响应函数

    def delete_button_clicked(self):
        selectedRow = []
        item = self.tableWidget.selectedItems()
        for i in item:
            if self.tableWidget.indexFromItem(i).row() not in selectedRow:
                selectedRow.append(self.tableWidget.indexFromItem(i).row())
        # print("self.selectedRow:",selectedRow)

        selected_date = []
        for temp in selectedRow:
            selected_date.append(self.tableWidget.item(temp,3).text())
        # print("读卡时间:",selected_date)

        conn = sqlite3.connect(dbname)
        conn.text_factory = str
        c = conn.cursor()
        for time_ in selected_date:
            c.execute("delete from identityInfo where currentDate=?",(time_,))
        conn.commit()
        c.close()
        select()
        self.tableWidget_insert_data()

    def name_check_button_clicked(self):   #点击按姓名查询按钮
        text = self.edit_name.text()
        # sys.stdout.write("点击按姓名查询按钮\n"+text)
        select1(text)    #查询
        self.tableWidget_insert_data()

    def ID_check_button_clicked(self):     #点击按ID查询
        text = self.edit_ID.text()
        # sys.stdout.write("点击按ID查询\n"+text)
        select2(text)
        self.tableWidget_insert_data()

    def time_check_button_clicked(self):   #点击按时间查询
        str1 = self.edit_time1.text()
        str2 = self.edit_time2.text()
        # sys.stdout.write("点击按时间查询\n"+str1+str2)
        select5(str1, str2)
        self.tableWidget_insert_data()

    def passed_check_button_clickd(self):  #验证通过查询
        # sys.stdout.write("验证通过查询\n")
        select3()
        self.tableWidget_insert_data()

    def unpassed_check_button_clicked(self): #验证未通过查询
        # sys.stdout.write("验证未通过查询\n")
        select4()
        self.tableWidget_insert_data()

    def tableWidget_insert_data(self):      #往表单中添加数据
        global list
        global count
        self.tableWidget.clearContents()
        self.tableWidget.setHorizontalHeaderLabels(['姓名', '性别','身份证号(ID)','读卡时间', '是否通过','民族', '生日','地址','签发机关','有效期','识别分数'])  # 添加表头

        # print ("往表单中添加数据输出list中内容")
        # print (list)
        len1 = len(list)
        self.tableWidget.setRowCount(len1)
        for i in range(len1):
            for j in range(10):
                newItem = QtGui.QTableWidgetItem(list[i][j])
                # print ("*",list[i][j])
                self.tableWidget.setItem(i,j,newItem)

    def export_button_clicked(self):        #点击导出按钮
        # sys.stdout.write("点击导出按钮\n")
        global count
        file = Workbook(encoding='utf-8')   # 指定file以utf-8的格式打开
        timestr = time.strftime('%Y_%m_%d.%H.%M.%S',time.localtime(time.time()))
        fileName_xls = '导出_' + timestr + '.xls'

        table = file.add_sheet(fileName_xls)       # 指定打开的文件名
        len1 = len(list)
        for i in range(len1):
            for j in range(10):
                # print items[item_index].text()
                 str = self.tableWidget.item(i, j).text()
                 table.write(i, j,str)
        file.save(fileName_xls)

class Ui_Face_Verification(object):     #主界面
    def __init__(self):
        ext_model_path = './model/facenet/inception-ring-1024.pb'
        self.video_capture = cv2.VideoCapture(camera_Id)
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
        self.unknownum = 0
        self.knownum = 0


        self.naivedlib = NaiveDlib()
        self.extractor = Extractor(ext_model_path,gpu_fraction=0)
        temp = np.ones((5, 112, 96, 1))
        self.extractor.extract_feature(im_arr=temp)
        self.query = deque(maxlen=2)
        self.start()

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

        pixmap2 = QtGui.QPixmap("logo.png")
        self.logo.setScaledContents(True)
        self.logo.setPixmap(pixmap2)


        #self.display_probe_image()
        self.start_verify()


        self.action_check.triggered.connect(self.check_Clicked)  # 设置信号 插槽的方法
        self.action_thresh.triggered.connect(self.threshold_clicked)

        self.action_camera_on.triggered.connect(self.camera_on_Clicked)  # 设置信号 插槽的方法
        self.action_camera_off.triggered.connect(self.camera_off_Clicked)


        #self.start_read_ID()

    def camera_on_Clicked(self):
        if self.is_camera_on == False:
            self.video_capture = cv2.VideoCapture(camera_Id)
            self.is_camera_on = True
            qtm = QtGui.QMessageBox
            msg_box = qtm(qtm.Warning, u"提示", u"打开摄像头成功!", qtm.Yes)  ##消息提示框
            msg_box.exec_()
        else:
            qtm = QtGui.QMessageBox
            msg_box = qtm(qtm.Warning, u"提示", u"摄像头已打开!", qtm.Yes)  ##消息提示框
            msg_box.exec_()

    def camera_off_Clicked(self):
        if self.is_camera_on == True:
            self.video_capture.release()
            self.is_camera_on = False
            qtm = QtGui.QMessageBox
            msg_box = qtm(qtm.Warning, u"提示", u"关闭摄像头成功!", qtm.Yes)  ##消息提示框
            msg_box.exec_()
        else:
            qtm = QtGui.QMessageBox
            msg_box = qtm(qtm.Warning, u"提示", u"摄像头已关闭!", qtm.Yes)  ##消息提示框
            msg_box.exec_()

    def check_Clicked(self):     #进入查询界面
        # app = QtWidgets.QApplication(sys.argv)
        Check_dlg = QtGui.QWidget()
        ui = Ui_ui_check()
        ui.setupUi(Check_dlg)
        Check_dlg.show()
        Check_dlg._exec()

    def threshold_clicked(self):    #进入阈值设置界面
        threshold_dlg = QtGui.QWidget()
        ui = Ui_threshold_setting()
        ui.setupUi(threshold_dlg)
        threshold_dlg.show()
        threshold_dlg._exec()

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

    # 识别比对
    def verify(self, thresh):
        global VIDEO_IMAGE
        global isPass
        flag = 0
        currentunknownum = 0
        currentknownum = 0
        idname = []  # 可显示id照片的编号列表
        currentDate = datetime.now().strftime('%Y_%m_%d')
        currentTime = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
        web = Web_Browser()
        web.setModal(False)
        web.setWindowTitle(_translate("Face_Verification", "比对结果", None))
        # if self.pic_time != None and (datetime.datetime.now() - self.pic_time).seconds > pic_time:
            # self.image_clear()

        with open('./data/index_enter.pkl', 'rb') as f:
            self.index_dict = pkl.load(f)
        self.feature_data = np.load('./data/database_enter.npy')
        #image1 = cv2.imread('./card/2.jpg')#加载图片测试
        image1 = self.probe_image
        #self.count = 2
        self.search_eign = Search_engin(self.feature_data)
        self.search_eign.train()
       # for i in range(VIDEO_IMAGE.qsize()):
           # image1 = VIDEO_IMAGE.get()
        if image1 is not None:
            print('get image')
            image1 = cv2.flip(image1, 1)
            width = int(image1.shape[1] / 2)
            height = int(image1.shape[0] / 2)
            image = cv2.resize(image1.copy(), (width, height))
            #if self.count % 1 == 0:
                #self.probe_image = image1.copy()
            try:
                    #total_start = time.time()
                    bboxs = self.naivedlib.getALLFaces(image)
                    #bbox_end = time.time()
                    print('bbox detect took ')
                    bboxs = [dlib.rectangle(int(bbox.left() * downsample_ratio), int(bbox.top() * downsample_ratio),
                                            int(bbox.right() * downsample_ratio), int(bbox.bottom() * downsample_ratio))
                             for bbox in bboxs]
                    facenum = len(bboxs)

                    print(facenum)#人脸数
                    # index_list = []
                    #idname = []  # 可显示id照片的编号列表
                    if bboxs is not None:
                        # print(time.strftime('%H:%M:%S', time.localtime(time.time())))
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
                            if score > thresh:
                                flag = 1
                                name = name_list[0]
                                idname.append(name)
                                print("欢迎" + name)
                                print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                                #web.write_result("比对成功")
                                #isPass = u'通过'

                                #self.id_image2 = cv2.imread('./user_pic/{}.bmp'.format(name))
                                #self.display_id_image2()
                                #cv2.imwrite('./image_saved/{}_1_{:>.2f}.jpg'.format(currentTime, score),save_croped)


                            else:
                                print("未知人员")
                                currentunknownum = currentunknownum + 1
                                #print(unknownum)
                                if not os.path.exists('./image_saved/{}'.format(currentDate)):
                                    os.mkdir('./image_saved/{}'.format(currentDate))
                                try:
                                    cv2.imwrite('./image_saved/{}/{}_{}.jpg'.format(currentDate, currentTime, currentunknownum),
                                                save_croped)

                                except:
                                    pass
                        if flag == 1:
                            print(idname)
                            currentknownum = len(idname)  # 当前已知访客数量
                            self.knownum = self.knownum + currentknownum


                            for i in range(currentknownum):
                                self.id_image = cv2.imread('./user_pic/{}.bmp'.format(idname[i]))
                                self.display_id_image(self.knownum)
                        if currentunknownum > 0:
                            print(currentunknownum)
                            self.unknownum = self.unknownum + currentunknownum
                            for i in range(currentunknownum):
                                self.id_image2 = cv2.imread('./image_saved/{}/{}_{}.jpg'.format(currentDate, currentTime, i+1))
                                self.display_id_image2(self.unknownum)

                    else:
                        web.write_result("未检测到人脸", 'red')
                        web.exec_()
                        self.clean_data()
            except:
                    pass
        else:
            pass


    def all_clean(self):
        self.id_image = None
        self.probe_image = None
        self.ID_label = 0
        self.ID_lib = {}
        self.ID_name = {}
        self.ID_photo.clear()
        self.Probe_photo.clear()
        self.id_image = None
        self.probe_image = None
        try:
            os.remove('./card/zp.bmp')
            os.remove('./card/ID_image/*')
        except:
            pass

    def display_probe_image(self):

        ret,image1 = self.video_capture.read()
        if ret:
            self.probe_image = image1.copy()

            try:
                bbox = self.naivedlib.getLargestFaceBoundingBox(image1)
                image1 = self.naivedlib.drawbbox(image1,bbox)
                if bbox:
                    image1 = cv2.rectangle(image1,(bbox.left(),bbox.top()),(bbox.right(),bbox.bottom()),[0,255,0],2)
            except:
                pass
            image = cv2.cvtColor(image1, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image,(320*2,240*2))
            # image = cv2.flip(image,1)
            image = QtGui.QImage(image, image.shape[1], \
                                 image.shape[0], image.shape[1] * 3, QtGui.QImage.Format_RGB888)
            pix = QtGui.QPixmap.fromImage(image)
            self.Probe_photo.setPixmap(pix)
        else:
            self.probe_image = None
            self.Probe_photo.setText(_translate("Face_Verification", "未读取到图片", None))
            self.Probe_photo.setStyleSheet('color: red')

    def read_ID_image(self):
        try:
            image = cv2.imread('./card/zp.bmp')
            self.id_image = image.copy()
            self.display_id_image()
        except:
            pass

    def clean_data(self):
        self.ID_photo.clear()
        self.Probe_photo.clear()
        self.id_image = None
        self.probe_image = None
        try:
            os.remove('./card/zp.bmp')
        except:
            pass

    def start(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.display_probe_image)
        self.timer.start(1000./24)

    def start_read_ID(self):
        self.timer2 = QtCore.QTimer()
        self.timer.timeout.connect(self.read_ID_image)
        self.timer.start(10)

    def start_verify(self):
        self.timer3 = QtCore.QTime()
        global thresh
        self.timer.timeout.connect(lambda: self.verify(thresh))
        self.timer.start(10)

    def Open_ID_Reader(self):
        # os.system('C:\\Users\\Gehen\\Desktop\\Face_Verify\\card\\ZKIDCardReader.exe')
        subprocess.Popen(r'card/ZKIDCardReader.exe')

    #获取txt文档信息
    def ID_information(self):
        global Name
        global sex
        global nation
        global BirDate
        global Address
        global CardID
        global Authority
        global Period
        global currentDate
        global isPass

        file = open('./card/wz.txt', 'rb')
        data = file.read()
        datacode = data.decode('utf-16')
        list = []
        list = datacode.split()

        Name = list[0]  # 姓名
        Part1 = list[1]
        sizeP1 = len(Part1)
        Gender = Part1[0:1]  # 性别 1男 2女'
        Nation = Part1[1:3]  # 民族
        BirDate = Part1[3:11]  # 出生日期
        Address = Part1[11:sizeP1]  # 住址
        Part2 = list[2]
        sizeP2 = len(Part2)
        CardID = Part2[0:18]  # 身份证号
        Authority = Part2[18:sizeP2]  # 签证机关
        Period = list[3]


        if Gender == '1':
            sex = u'男'
        elif Gender == '2':
            sex = u'女'
        if Nation == '01':
            nation = u'汉'
        elif Nation == '02':
            nation = u'蒙古'
        elif Nation == '03':
            nation = u'回'
        elif Nation == '04':
            nation = u'藏'
        elif Nation == '05':
            nation = u'维吾尔'
        elif Nation == '06':
            nation = u'苗'
        elif Nation == '07':
            nation = u'彝'
        elif Nation == '08':
            nation = u'壮'
        elif Nation == '09':
            nation = u'布依'
        elif Nation == '10':
            nation = u'朝鲜'
        elif Nation == '11':
            nation = u'满'
        self.label_name.setText(Name)
        self.label_sex.setText(sex)
        self.label_nation.setText(nation)

        birth = BirDate[0] + BirDate[1] + BirDate[2] + BirDate[3] + '-' + BirDate[4] + BirDate[5] + '-' + BirDate[6] + \
                BirDate[7]
        self.label_birth.setText(birth)
        self.label_address.setText(Address)
        self.label_ID.setText(CardID)
        self.label_authority.setText(Authority)
        # self.label_date.setText(Period)  # 有效期
        QtCore.QTimer.singleShot(2000, self.clear_text)  # 身份证信息停留10秒
    def clear_text(self):
        self.label_name.clear()
        self.label_sex.clear()
        self.label_nation.clear()
        self.label_birth.clear()
        self.label_address.clear()
        self.label_ID.clear()
        self.label_authority.clear()

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


class QtCapture(QtGui.QWidget):
    def __init__(self, cap, label):
        # super(QtGui.QWidget, self).__init__()
        self.fps = 24
        self.cap = cap
        self.video_frame = label

    def nextFrameSlot(self):
        ret, frame = self.cap.read()
        # OpenCV yields frames in BGR format
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        img = QtGui.QImage(frame, frame.shape[1], frame.shape[0], QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(img)
        self.video_frame.setPixmap(pix)



# 建表
def create_tables(dbname):
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    try:
        create_table = '''create table if not exists identityInfo
              (id integer primary key autoincrement not null,
                name text not null,
                   gender text not null,
                   nation text not null,
                   birDate text not null,
                   address char(80),
                   cardID char(18) not null,
                   authority char(50),
                   period text,
                   currentDate datetime,
                   isPass text
                   score FLOAT);'''
        c.execute(create_table)
        print("Table created successfuly")
    except:
        print ("Table createx failed")
    conn.commit()
    c.close()
    conn.close()

#插入数据
def insert(score):
    global Name
    global sex
    global nation
    global BirDate
    global Address
    global CardID
    global Authority
    global Period
    global currentDate
    global isPass
    global IDPhoto
    global photo
    global thresh

    conn = sqlite3.connect(dbname)
    conn.text_factory = str
    c = conn.cursor()

    c.execute("insert into identityInfo\
          (name,gender,nation,birDate,address,cardID,authority,period,currentDate,isPass,score)\
           values (?,?,?,?,?,?,?,?,?,?,?)",(Name,sex,nation,BirDate,Address,CardID,Authority,Period,currentDate,isPass,score))

    conn.commit()
    c.close()
    conn.close()
    # print ("Records created successfully")


#查询
def select():
    global list
    global count
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    cursor = c.execute("select name, gender, cardID,currentDate, isPass, nation, birDate, address,  authority, period, score from identityInfo order by currentDate DESC ")
    # print("测试：输出数据库所有信息")
    # for row in cursor:
    #     print (row)
    list.clear()
    for row in cursor:
        list.append(row)
        # print("name = ", row[0], "\n")
    # print("Select1 Operation done successfully")

#按姓名查询
def select1(text):
    global list
    global count
    conn = sqlite3.connect(dbname)
    conn.text_factory = str
    c = conn.cursor()

    cursor = c.execute("select name, gender, cardID,currentDate, isPass, nation, birDate, address,  authority, period, score from identityInfo where name = ?", (text,))
    list.clear()
    for row in cursor:
        list.append(row)
        # print("name = ", row[0], "\n")
        # print("Select1 Operation done successfully")


#身份证号查询
def select2(text):
    global list
    global count
    conn = sqlite3.connect(dbname)
    conn.text_factory = str
    c = conn.cursor()
    # print ("select name,cardID,currentDate,isPass from identitiInfo where cardID = '%s'" % text)
    cursor = c.execute("select name, gender, cardID,currentDate, isPass, nation, birDate, address,  authority, period, score from identityInfo where cardID = ?", (text,))

    list.clear()
    for row in cursor:
        list.append(row)
        # print("name = ", row[0], "\n")
        # print("Select1 Operation done successfully")


#通过查询
def select3():
    global list
    global count
    conn = sqlite3.connect(dbname)
    conn.text_factory = str
    c = conn.cursor()
    cursor = c.execute("select name, gender, cardID,currentDate, isPass, nation, birDate, address,  authority, period, score from identityInfo where isPass = '通过'")

    list.clear()
    for row in cursor:
        list.append(row)
        # print("name = ", row[0], "\n")
        # print("Select1 Operation done successfully")

#未通过查询
def select4():
    global list
    global count
    conn = sqlite3.connect(dbname)
    conn.text_factory = str
    c = conn.cursor()
    cursor = c.execute("select name, gender, cardID,currentDate, isPass, nation, birDate, address,  authority, period, score from identityInfo where isPass = '未通过'")

    list.clear()
    for row in cursor:
        list.append(row)
        # print("name = ", row[0], "\n")
        # print("Select1 Operation done successfully")

#按刷卡日期查询
def select5(start,end):
    global list
    global count
    conn = sqlite3.connect(dbname)
    conn.text_factory = str
    c = conn.cursor()
    cursor = c.execute("select name, gender, cardID,currentDate, isPass, nation, birDate, address,  authority, period, score from identityInfo "
                       "where date(currentDate) BETWEEN date(?) and date(?)",(start,end,))
    list.clear()
    for row in cursor:
        list.append(row)
        # print("name = ", row[0], "\n")
        # print("Select1 Operation done successfully")

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

#阈值设置
def read_thresh():
    global thresh
    file = open('./thresh.txt', 'rb')
    data = file.read().decode('utf-8')
    thresh = data

def write_thresh():
    global thresh
    file = open('./thresh.txt', 'w')
    file.write(str(thresh))


if __name__ == "__main__":

    dbname = 'test.db'
    create_tables(dbname)
    code()            #授权码

    app = QtGui.QApplication(sys.argv)
    read_thresh()

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
    # 创建数据库

    # os.mknod("checklog.txt")

    if stri == License:
        #设置界面风格
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))  # Windows   WindowsXP   WindowsVista   Motif   CDE   Plastique   Cleanlooks
        # QtGui.QApplication.setPalette(QtGui.QApplication.style().standardPalette())    #设置成风格的标准颜色
        Face_Verification = QtGui.QMainWindow()
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

    if isCheck:
        # license.exec_()
        QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))  # Windows   WindowsXP   WindowsVista   Motif   CDE   Plastique   Cleanlooks
        # QtGui.QApplication.setPalette(QtGui.QApplication.style().standardPalette())    #设置成风格的标准颜色
        Face_Verification = QtGui.QMainWindow()
        ui = Ui_Face_Verification()
        ui.setupUi(Face_Verification)
        Face_Verification.show()

    sys.exit(app.exec_())

