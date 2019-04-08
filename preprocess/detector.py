import tensorflow as tf
import detect_util
import numpy as np
from tensorflow.python.platform import gfile
import time
import cv2

def imresample(img, sz):
    im_data = cv2.resize(img, (sz[1], sz[0]), interpolation=cv2.INTER_AREA) #@UndefinedVariable
    return im_data

class Detector:
    def __init__(self, model_path, gpu_fraction,
                 min_size=20, thresh_list=[0.6, 0.7, 0.7], factor=0.709, scale=0.7):
        config = tf.ConfigProto()
        config.gpu_options.per_process_gpu_memory_fraction = gpu_fraction
        with tf.Graph().as_default():
            with gfile.FastGFile(model_path, 'rb') as f:
                    graph_def = tf.get_default_graph().as_graph_def()
                    graph_def.ParseFromString(f.read())
                    tf.import_graph_def(graph_def)
            self.sess = tf.Session(config=config)
            # gd = tf.get_default_graph().as_graph_def()
            # for v in gd.node:
            #     print v.name
        self.min_size = min_size
        self.thresh_list = thresh_list
        self.factor = factor
        self.scale = scale

    def close(self):
        self.sess.close()


    def detect_face(self, img, debug=False):
        """
        :param img:input image, load by opencv
        :return: result
        """
        factor_count = 0
        total_boxes = np.empty((0, 9))
        points = []
        h = img.shape[0]
        w = img.shape[1]
        minl = np.amin([h, w])
        m = 12.0 / self.min_size
        minl = minl * m
        # creat scale pyramid
        scales = []
        while minl >= 12:
            scales += [m * np.power(self.factor, factor_count)]
            minl = minl * self.factor
            factor_count += 1
        # first stage
        for j in xrange(len(scales)):
            scale = scales[j]
            hs = int(np.ceil(h * scale))
            ws = int(np.ceil(w * scale))
            im_data = imresample(img, (hs, ws))
            im_data = (im_data - 127.5) * 0.0078125
            im_data = np.transpose(np.expand_dims(im_data, 0), (0, 2, 1, 3))
            start = time.time()
            out = self.sess.run(('import/pnet/conv4-2/BiasAdd:0', 'import/pnet/prob1:0'), feed_dict={'import/pnet/input:0': im_data})
            # print("pnet time {} s".format(time.time()-start))
            out0 = np.transpose(out[0], (0, 2, 1, 3))
            out1 = np.transpose(out[1], (0, 2, 1, 3))

            boxes, _ = detect_util.generateBoundingBox(out1[0, :, :, 1], out0[0, :, :, :], scale, self.thresh_list[0])

            # inter-scale nms
            pick = detect_util.nms(boxes.copy(), 0.5, 'Union')
            if boxes.size > 0 and pick.size > 0:
                boxes = boxes[pick, :]
                total_boxes = np.append(total_boxes, boxes, axis=0)

        numbox = total_boxes.shape[0]
        if numbox > 0:
            pick = detect_util.nms(total_boxes.copy(), 0.7, 'Union')
            total_boxes = total_boxes[pick, :]
            regw = total_boxes[:, 2] - total_boxes[:, 0]
            regh = total_boxes[:, 3] - total_boxes[:, 1]
            qq1 = total_boxes[:, 0] + total_boxes[:, 5] * regw
            qq2 = total_boxes[:, 1] + total_boxes[:, 6] * regh
            qq3 = total_boxes[:, 2] + total_boxes[:, 7] * regw
            qq4 = total_boxes[:, 3] + total_boxes[:, 8] * regh
            total_boxes = np.transpose(np.vstack([qq1, qq2, qq3, qq4, total_boxes[:, 4]]))
            total_boxes = detect_util.rerec(total_boxes.copy())
            total_boxes[:, 0:4] = np.fix(total_boxes[:, 0:4]).astype(np.int32)
            dy, edy, dx, edx, y, ey, x, ex, tmpw, tmph = detect_util.pad(total_boxes.copy(), w, h)

        numbox = total_boxes.shape[0]
        if numbox > 0:
            # second stage
            tempimg = np.zeros((24, 24, 3, numbox))
            for k in xrange(0, numbox):
                tmp = np.zeros((int(tmph[k]), int(tmpw[k]), 3))
                tmp[dy[k] - 1:edy[k], dx[k] - 1:edx[k], :] = img[y[k] - 1:ey[k], x[k] - 1:ex[k], :]
                if tmp.shape[0] > 0 and tmp.shape[1] > 0 or tmp.shape[0] == 0 and tmp.shape[1] == 0:
                    tempimg[:, :, :, k] = imresample(tmp, (24, 24))
                else:
                    return np.empty()
            tempimg = (tempimg - 127.5) * 0.0078125
            tempimg = np.transpose(tempimg, (3, 1, 0, 2))
            start = time.time()
            out = self.sess.run(('import/rnet/conv5-2/conv5-2:0', 'import/rnet/prob1:0'), feed_dict={'import/rnet/input:0': tempimg})
            # print("rnet time {} s".format(time.time()-start))
            out0 = np.transpose(out[0])
            out1 = np.transpose(out[1])
            score = out1[1, :]
            ipass = np.where(score > self.thresh_list[1])
            total_boxes = np.hstack([total_boxes[ipass[0], 0:4].copy(), np.expand_dims(score[ipass].copy(), 1)])
            mv = out0[:, ipass[0]]
            if total_boxes.shape[0] > 0:
                pick = detect_util.nms(total_boxes, 0.7, 'Union')
                total_boxes = total_boxes[pick, :]
                total_boxes = detect_util.bbreg(total_boxes.copy(), np.transpose(mv[:, pick]))
                total_boxes = detect_util.rerec(total_boxes.copy())

        numbox = total_boxes.shape[0]
        if numbox > 0:
            # third stage
            total_boxes = np.fix(total_boxes).astype(np.int32)
            dy, edy, dx, edx, y, ey, x, ex, tmpw, tmph = detect_util.pad(total_boxes.copy(), w, h)
            tempimg = np.zeros((48, 48, 3, numbox))
            for k in xrange(0, numbox):
                tmp = np.zeros((int(tmph[k]), int(tmpw[k]), 3))
                tmp[dy[k] - 1:edy[k], dx[k] - 1:edx[k], :] = img[y[k] - 1:ey[k], x[k] - 1:ex[k], :]
                if tmp.shape[0] > 0 and tmp.shape[1] > 0 or tmp.shape[0] == 0 and tmp.shape[1] == 0:
                    tempimg[:, :, :, k] = imresample(tmp, (48, 48))
                else:
                    return np.empty()
            tempimg = (tempimg - 127.5) * 0.0078125
            tempimg = np.transpose(tempimg, (3, 1, 0, 2))
            start = time.time()
            out = self.sess.run(('import/onet/conv6-2/conv6-2:0', 'import/onet/conv6-3/conv6-3:0', 'import/onet/prob1:0'), feed_dict={'import/onet/input:0': tempimg})
            # print("onet time {} s".format(time.time()-start))
            out0 = np.transpose(out[0])
            out1 = np.transpose(out[1])
            out2 = np.transpose(out[2])
            score = out2[1, :]
            points = out1
            ipass = np.where(score > self.thresh_list[2])
            points = points[:, ipass[0]]
            total_boxes = np.hstack([total_boxes[ipass[0], 0:4].copy(), np.expand_dims(score[ipass].copy(), 1)])
            mv = out0[:, ipass[0]]

            w = total_boxes[:, 2] - total_boxes[:, 0] + 1
            h = total_boxes[:, 3] - total_boxes[:, 1] + 1
            points[0:5, :] = np.tile(w, (5, 1)) * points[0:5, :] + np.tile(total_boxes[:, 0], (5, 1)) - 1
            points[5:10, :] = np.tile(h, (5, 1)) * points[5:10, :] + np.tile(total_boxes[:, 1], (5, 1)) - 1
            if total_boxes.shape[0] > 0:
                total_boxes = detect_util.bbreg(total_boxes.copy(), np.transpose(mv))
                pick = detect_util.nms(total_boxes.copy(), 0.7, 'Min')
                total_boxes = total_boxes[pick, :]
                points = points[:, pick]

        result = []
        if debug:
            debug_img = img.copy()
        for bb, point in zip(total_boxes, np.transpose(points)):
            result_dic = {}
            result_dic['bbox'] = list(bb[:4])  # left_x, up_y, right_x, down_y
            result_dic['area'] = (bb[2] - bb[0]) * (bb[3] - bb[1])
            result_dic['score'] = bb[4]
            result_dic['left_eye'] = [point[0], point[5]]
            result_dic['right_eye'] = [point[1], point[6]]
            result_dic['nose'] = [point[2], point[7]]
            result_dic['left_mouth'] = [point[3], point[8]]
            result_dic['right_mouth'] = [point[4], point[9]]
            result_dic['width'] = bb[2] - bb[0]
            result_dic['height'] = bb[3] - bb[1]
            result.append(result_dic)
            if debug:
                cv2.rectangle(debug_img, (int(bb[0]), int(bb[1])), (int(bb[2]), int(bb[3])), (0, 255, 0), 2)
                cv2.circle(debug_img, tuple(result_dic['left_eye']), 1, (255, 0, 0), 2)
                cv2.circle(debug_img, tuple(result_dic['right_eye']), 1, (255, 0, 0), 2)
                cv2.circle(debug_img, tuple(result_dic['nose']), 1, (255, 0, 0), 2)
                cv2.circle(debug_img, tuple(result_dic['left_mouth']), 1, (255, 0, 0), 2)
                cv2.circle(debug_img, tuple(result_dic['right_mouth']), 1, (255, 0, 0), 2)
        if debug:
            cv2.imwrite('debug.jpg', debug_img)
        return result

if __name__ == '__main__':
    model_path = 'face_detector.pb'
    im = cv2.imread('test.jpg')
    start = time.time()
    detector = Detector(model_path, gpu_fraction=0.002)
    print("init in {} s".format(time.time() - start))

    while True:
        start = time.time()
        result = detector.detect_face(im, debug=True)
        print("finish in {} s".format(time.time() - start))


