from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os 
import tensorflow as tf
from tensorflow.python.platform import gfile
from collections import deque
from scipy import spatial
import time
import numpy as np
import cv2, dlib
from preprocess.crop_util_search import crop_rotate_v2
from preprocess.image_preprocess import proc_img
from PIL import Image
# import matplotlib.pyplot as plt


class Extractor:
    def __init__(self, model_path, gpu_fraction):
        print("Start to Load feature extractor model")
        start = time.time()
        config = tf.ConfigProto()
        config.gpu_options.per_process_gpu_memory_fraction = gpu_fraction
        self.gragh = tf.Graph()
        self.sess = tf.Session(config=config, graph=self.gragh)
        with self.gragh.as_default():
            self.image_placeholder = tf.placeholder(tf.float32, shape=(None, 112, 96, 1), name='images')
            print('Loading graphdef: %s' % model_path)
            with gfile.FastGFile(model_path, 'rb') as f:
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(f.read())
                return_elements = ['phase_train:0', 'embedding:0']
                self.phase_train, self.embedding = tf.import_graph_def(graph_def, return_elements=return_elements,
                                                     input_map={'images': self.image_placeholder})
        print("finish load model in {} s".format(time.time() - start))

    def preprocess_imgage(self,image,naivedlib):
        bbox = naivedlib.getLargestFaceBoundingBox(image)
        if bbox is not None:
            query = []
            left_eye, right_eye = naivedlib.get_eyes(image, bbox)
            crop_image = crop_rotate_v2(image[:, :, ::-1], left_eye, right_eye,
                                        bbox.width() * 0.895)
            flip_image = cv2.flip(crop_image.copy(), 1)
            crop_image = proc_img(crop_image, is_whiten=False)
            flip_image = proc_img(flip_image, is_whiten=False)
            query.append(crop_image[0])
            query.append(flip_image[0])
            prob_image = np.asarray(query)
            return prob_image
        else:
            return None

    def extract_feature(self, im_arr):
        emb_fea = self.sess.run([self.embedding], feed_dict={self.image_placeholder: im_arr, self.phase_train: False})[0]
        #print(emb_fea)
        emb_fea = np.mean(emb_fea,0)  # 对各列求均值
        return emb_fea

    def cal_score(self,fea_house):
        score_list = []
        ID_fea = fea_house[0]
        prob_fea = fea_house[1:]
        for i in range(len(prob_fea)):
            score = 1-spatial.distance.cosine(ID_fea,prob_fea[i])
            score_list.append(score)
        final_score = sum(score_list)/len(score_list)
        return final_score

    def search_face(self,probe_fea,id_features,thresh=0.6):
        score_list = []
        num = id_features.shape[0]
        for i in range(num):
            id_fea = id_features[i]
            score = 1-spatial.distance.cosine(id_fea,probe_fea)
            score_list.append(score)
        temp_target = score_list.index(max(score_list))
        score = score_list[temp_target]
        return temp_target, score
        # if not score<thresh:
        #
        # else:
        #     return None,None

    def close(self):
        self.sess.close()
        
class NaiveDlib:
    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()  # 利用 Dlib 的特征提取器，进行人脸 矩形框 的提取
        self.predictor = dlib.shape_predictor('./model/dlib/shape_predictor_68_face_landmarks.dat')
        #利用 Dlib 的68点特征预测器，进行人脸 面部轮廓特征 提取

    def getALLFaces(self, img):
        faces = self.detector(img, 0)
        if len(faces) > 0:
            return faces
        else:
            return None

    def getLargestFaceBoundingBox(self,img):
        faces = self.detector(img,0)
        if len(faces)>0:
            return max(faces,key=lambda rect:rect.width()*rect.height())
        else:
            return None
    
    def get_eyes(self,img,bbox):
        landmarks = self.predictor(img,bbox)
        left_eye_l = [landmarks.part(36).x,landmarks.part(36).y]
        left_eye_r = [landmarks.part(39).x,landmarks.part(39).y]
        left_eye = list(map(int,(np.array(left_eye_l)+np.array(left_eye_r))/2))
        right_eye_l = [landmarks.part(42).x,landmarks.part(42).y]
        right_eye_r = [landmarks.part(45).x,landmarks.part(45).y]
        right_eye = list(map(int,(np.array(right_eye_l)+np.array(right_eye_r))/2))
        return left_eye,right_eye
        
    def drawbbox(self,img,bb):
        cv2.rectangle(img,(bb.left(),bb.top()),(bb.right(),bb.bottom()),(0,255,0),2)
        return img
    def drawbboxs(self, img, bbs):
        for bb in bbs:
            cv2.rectangle(img, (bb.left(), bb.top()), (bb.right(), bb.bottom()), (0, 255, 0), 2)
        return img
    

if __name__ == "__main__":
    from preprocess.crop_util_search import crop_rotate_part
    naivedlib = NaiveDlib()
    downsample_ratio = 2
    #ext_model_path = './model/facenet/inception-ring-1024.pb'
    #extractor = Extractor(ext_model_path, gpu_fraction=0)  # gpu_fraction显存占用比例
    #temp = np.ones((5, 112, 96, 1))
    #extractor.extract_feature(im_arr=temp)
    image1 = cv2.imread('./card/2.jpg')  # 加载图片测试
    bboxs = naivedlib.getALLFaces(image1)
    img = naivedlib.drawbboxs(image1,bboxs)
    cv2.imwrite('box.jpg', img)
   # cv2.imshow("image", img)
