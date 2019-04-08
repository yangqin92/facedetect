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
import cv2
import dlib
from preprocess.crop_util import crop_rotate_v2
from preprocess.image_preprocess import proc_img
import matplotlib.pyplot as plt


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

    def extract_feature(self, im_arr):
        emb_fea = self.sess.run([self.embedding], feed_dict={self.image_placeholder: im_arr, self.phase_train: False})[0]
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

    def search_face(self,probe_fea,ID_feas,thresh=0.55):
        score_dict = {}
        person_list = ID_feas.keys()
        for person in person_list:
            ID_fea = ID_feas[person]
            temp_fea = np.concatenate((ID_fea,probe_fea),axis=0)
            score = self.cal_score(temp_fea)
            score_dict[person] = score
        temp_target = max(score_dict,key=lambda x:score_dict[x])
        score = score_dict[temp_target]
        if not score<thresh:
            return temp_target
        else:
            return None
    
    def close(self):
        self.sess.close()
        
class NaiveDlib:
    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor('./model/dlib/shape_predictor_68_face_landmarks.dat')
    
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
    
    

if __name__ == "__main__":
    from PIL import Image 
#    from preprocess.detector import Detector

    
    video_capture = cv2.VideoCapture(0)
    naivedlib = NaiveDlib()
    ext_model_path = './model/facenet/inception-ring-1024.pb'
    extractor = Extractor(ext_model_path, gpu_fraction=0.5)
    query = deque(maxlen=4)
    if os.path.isfile('./card/zp.bmp'):
        os.remove('./card/zp.bmp')
    
    start = time.time()
    temp = np.ones((5,112,96,1))
    extractor.extract_feature(im_arr=temp)
    end = time.time()
    print ('Init network took {:.3f}s'.format(end-start))
    
    thresh = 0.5
    
    count = 10
    person_status = ''
    while True:
        ret,img = video_capture.read()
        imgshow = img.copy()
        try:
            start = time.time()
            bbox = naivedlib.getLargestFaceBoundingBox(img)
            left_eye ,right_eye = naivedlib.get_eyes(img,bbox)
            crop_image = crop_rotate_v2(img[:, :, ::-1], left_eye, right_eye,
                                        bbox.width()*1.0)
            flip_image = cv2.flip(crop_image.copy(),1)
            
            crop_image = proc_img(crop_image, is_whiten=False)
            flip_image = proc_img(flip_image, is_whiten=False)
            
            query.append(crop_image[0])
            query.append(flip_image[0])
            end = time.time()
#            print ('detect face took {:.3f}s'.format(end-start))
            imgshow = naivedlib.drawbbox(imgshow,bbox)   
            score = 1
            if os.path.isfile('./card/zp.bmp') and len(query)>3:
                ID_image = cv2.imread('./card/zp.bmp')
                ID_bbox = naivedlib.getLargestFaceBoundingBox(ID_image)
                ID_left_eye ,ID_right_eye = naivedlib.get_eyes(ID_image,ID_bbox)
                ID_crop_image = crop_rotate_v2(ID_image[:, :, ::-1], ID_left_eye, ID_right_eye,
                                ID_bbox.width()*1.03)
                ID_crop_image = proc_img(ID_crop_image, is_whiten=False)
                
                prob_image = np.asarray(query)
                crop_house = np.concatenate((ID_crop_image,prob_image),axis=0)
                start = time.time()
                fea_house = extractor.extract_feature(im_arr=crop_house)
                score = extractor.cal_score(fea_house)
                end = time.time()
                print ('extract feature took {:.3f}s'.format(end-start))
                print ('similarity is {:.3f}'.format(score))
                os.remove('./card/zp.bmp')
                
                if score>thresh:
                    color = [0,255,0]
                    person_status = 'Same Person'
                else:
                    color = [0,0,255]
                    person_status = 'Different Person'
                count = 0
            if count<=10:
                cv2.putText(imgshow,person_status,(bbox.left(),bbox.top()-10),cv2.FONT_HERSHEY_COMPLEX,1,color,2)
                cv2.rectangle(imgshow,(bbox.left(),bbox.top()),(bbox.right(),bbox.bottom()),color,2)
            count += 1
        except:
            pass
        try:
            cv2.imshow('Face Verifaction',imgshow)
        except:
            pass
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            if os.path.isfile('./card/zp.bmp'):
                os.remove('./card/zp.bmp')
            video_capture.release()
            extractor.close()
            break

        
#        