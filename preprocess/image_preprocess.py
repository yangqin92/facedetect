# coding=utf-8
# image_preprocess.py: 图像预处理文件

import numpy as np

def to_rgb(img):
    """
    :参数 img: 灰度图，采用 misc 读取
    :返回值: 3通道彩色图
    """
    w, h = img.shape
    ret = np.empty((w, h, 3), dtype=np.uint8)
    ret[:, :, 0] = ret[:, :, 1] = ret[:, :, 2] = img
    return ret

def proc_img(im_arr, is_scale=True, is_whiten=True, is_newaxis=True):
    """
    ：参数 im_arr：[0:255]范围间的三通道或二通道 ndarray 格式的图片
          is_scale: 是否转换为[-1,1]
          is_whiten: 是否白化
    ：返回值
          预处理后的图片
    """
    pre_img = im_arr.copy()
    if is_scale:
        pre_img = pre_img.astype(np.float32) / 255.0
        pre_img = (pre_img - 0.5) * 2.0
    if is_whiten:
        mean = np.mean(pre_img)
        std = np.std(pre_img)
        std_adj = np.maximum(std, 1.0 / np.sqrt(pre_img.size))
        pre_img = np.multiply(np.subtract(pre_img, mean), 1 / std_adj)
    if is_newaxis:
        if pre_img.ndim == 2:
            pre_img = pre_img[np.newaxis, :, :, np.newaxis]
        elif pre_img.ndim == 3:
            pre_img = pre_img[np.newaxis, :, :, :]
        else:
            raise Exception("wrong dimention")
    return pre_img
