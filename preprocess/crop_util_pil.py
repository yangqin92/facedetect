"""
this script is use landmark to do similiar transform for detected face
"""
from PIL import Image, ImageDraw
from preprocess.image_preprocess import proc_img
import math
import numpy as np
import cv2


def Distance(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx*dx+dy*dy)


def cal_mid(p1, p2):
    m_x = (p2[0] + p1[0]) / 2.0
    m_y = (p2[1] + p1[1]) / 2.0
    return m_x, m_y


def transfer(origin_point, rotate_angle, point):
    dis = Distance(origin_point, point)
    direction = (point[0] - origin_point[0], point[1] - origin_point[1])
    origin_angle = math.atan2(float(direction[1]), float(direction[0]))
    angle = origin_angle + rotate_angle
    x = origin_point[0] + math.cos(angle) * dis
    y = origin_point[1] + math.sin(angle) * dis
    return x, y


def ScaleRotateTranslate(image, angle, center=None, new_center=None,
                         scale=None, resample=Image.BICUBIC):
    if (scale is None) and (center is None):
        return image.rotate(angle=angle, resample=resample)
    new_x, new_y = x, y = center
    scale_x = scale_y = 1.0
    if new_center:
        (new_x, new_y) = new_center
    if scale:
        (scale_x, scale_y) = (scale, scale)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    a = cosine/scale_x
    b = sine/scale_x
    c = x-new_x*a-new_y*b
    d = -sine/scale_y
    e = cosine/scale_y
    f = y-new_x*d-new_y*e
    return image.transform(image.size, Image.AFFINE,
                           (a, b, c, d, e, f), resample=resample)


def crop_rotate(image, eye_left=(0, 0), eye_right=(0, 0), bb_width=10,
                extend=0.2, dest_sz=(96, 112)):
    """
    this function is used to do similarity transformation,
    put the eye into horizontal direction
    and make the eye in the same position
    """
    image = Image.fromarray(image)
    # calculate mid_point of two eyes
    mid_eye = cal_mid(eye_left, eye_right)
    # calculate the rotation angel
    eye_direction = (eye_right[0] - eye_left[0], eye_right[1] - eye_left[1])
    rotation = -math.atan2(float(eye_direction[1]), float(eye_direction[0]))
    # scale factor 1/scale is how the final image change
    scale = float(bb_width*1.02) / float(dest_sz[0]) # the width of bbox keeps unchange
    # rotate original around the left eye, rotate the image without scale
    image = ScaleRotateTranslate(image, center=mid_eye, angle=rotation)
    # calculate aspect ratio
    a_ratio = 1.0 * dest_sz[1] / dest_sz[0]
    # crop the rotated image,the coodinate of middle of eyes is fixed
    crop_xy = (mid_eye[0] - bb_width / 2.0, mid_eye[1] - bb_width * a_ratio * extend)
    crop_size = (dest_sz[0]*scale, dest_sz[1]*scale)
    image = image.crop((int(crop_xy[0]), int(crop_xy[1]), int(crop_xy[0]+crop_size[0]),
                        int(crop_xy[1]+crop_size[1])))
    # resize it
    image = image.resize(dest_sz, Image.ANTIALIAS)
    image = image.convert('L')
    image = np.array(image)
    return image


def crop_rotate_v2(image, eye_left, eye_right, bb_width, is_gray=True,
                   dest_width=85, extend=0.3, dest_sz=(96, 112)):
    """
    this function is used to do similarity transformation,
    put the eye into horizontal direction
    and make the eye in the same position
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    # calculate mid_point of two eyes
    mid_eye = cal_mid(eye_left, eye_right)
    scale = bb_width / dest_width  # the width of bbox keeps unchange

    # calculate the rotation angel
    eye_direction = (eye_right[0] - eye_left[0], eye_right[1] - eye_left[1])
    rotation = -math.atan2(float(eye_direction[1]), float(eye_direction[0]))

    # rotate original around the left eye, rotate the image without scale
    image = ScaleRotateTranslate(image, center=mid_eye, angle=rotation)

    raw_width = dest_sz[0] * scale
    raw_height = dest_sz[1] * scale

    # crop the rotated image,the coodinate of middle of eyes is fixed
    crop_xy = (mid_eye[0] - raw_width / 2.0, mid_eye[1] - raw_height * extend)
    image = image.crop((int(crop_xy[0]), int(crop_xy[1]), int(crop_xy[0]+raw_width),
                        int(crop_xy[1]+raw_height)))
    # resize it
    image = image.resize(dest_sz, Image.ANTIALIAS)
    if is_gray:
        image = image.convert('L')
    image = np.array(image)
    return image


def crop_rotate_v3(image_temp, result, is_gray=True,
                   dest_width=85, extend=0.3, dest_sz=(96, 112), dest_p_sz=(64, 64)):
    """
    this function is used to do similarity transformation,
    put the eye into horizontal direction
    and make the eye in the same position
    """

    eye_left = result['left_eye']
    eye_right = result['right_eye']
    bb_width = result['width']
    nose = result['nose']
    mouth_left = result['left_mouth']
    mouth_right = result['right_mouth']

    point_list = [eye_left, eye_right, nose, mouth_left, mouth_right]

    if isinstance(image_temp, np.ndarray):
        image_temp = Image.fromarray(image_temp)
    # calculate mid_point of two eyes
    mid_eye = cal_mid(eye_left, eye_right)
    scale = bb_width / dest_width  # the width of bbox keeps unchange

    # calculate the rotation angel
    eye_direction = (eye_right[0] - eye_left[0], eye_right[1] - eye_left[1])
    rotation = -math.atan2(float(eye_direction[1]), float(eye_direction[0]))

    # rotate original around the left eye, rotate the image without scale
    image_temp = ScaleRotateTranslate(image_temp, center=mid_eye, angle=rotation)
    point_list_r = [transfer(mid_eye, rotation, i) for i in point_list]

    # draw = ImageDraw.Draw(image)
    # r = 1
    # for point in point_list_r:
    #     draw.ellipse((point[0] - r, point[1] - r, point[0] + r, point[1] + r))

    raw_width = dest_sz[0] * scale
    raw_height = dest_sz[1] * scale
    raw_p_width = dest_p_sz[0] * scale
    raw_p_height = dest_p_sz[1] * scale

    if is_gray:
        image_temp = image_temp.convert('L')

    part_list = []
    for point in point_list_r:
        crop_xy = (point[0] - raw_p_width / 2.0, point[1] - raw_p_height / 2.0)
        p_image = image_temp.crop((int(crop_xy[0]), int(crop_xy[1]), int(crop_xy[0] + raw_p_width),
                              int(crop_xy[1] + raw_p_height)))
        p_image = p_image.resize(dest_p_sz, Image.ANTIALIAS)
        part_list.append(p_image)

    # resize it
    crop_xy = (mid_eye[0] - raw_width / 2.0, mid_eye[1] - raw_height * extend)
    crop_image = image_temp.crop((int(crop_xy[0]), int(crop_xy[1]), int(crop_xy[0]+raw_width),
                             int(crop_xy[1]+raw_height)))
    crop_image = crop_image.resize(dest_sz, Image.ANTIALIAS)


    ####
    temp = [crop_image]
    temp.extend(part_list)
    [full_l, eye_l, eye_r, nose_l, mouth_l, mouth_r] = [np.asarray(item) for item in
                                                        temp]
    full_r = cv2.flip(full_l, 1)
    nose_r = cv2.flip(nose_l, 1)
    [full_l, full_r, eye_l, eye_r, nose_l, nose_r, mouth_l, mouth_r] = [proc_img(item) for item in
                                                                        [full_l, full_r, eye_l, eye_r, nose_l, nose_r,
                                                                         mouth_l, mouth_r]]
    # [eye_l, eye_r, mouth_l, mouth_r] = [np.reshape(item, (1, 64, 64, 1)) for item in [eye_l, eye_r, mouth_l, mouth_r]]
    # [nose_l, nose_r] = [np.reshape(item, (1, 64, 64, 1)) for item in [nose_l, nose_r]]
    # [full_l, full_r] = [np.reshape(item, (1, 112, 96, 1)) for item in [full_l, full_r]]
    ####

    return [full_l,full_r,eye_l, eye_r, nose_l,nose_r, mouth_l, mouth_r]


def crop_only(image, bb, dest_width=85, extend=0.4,
              is_gray=True, dest_sz=(96, 112)):
    """
    bbox should be left up right bottom
    this function is used to do similarity transformation,
    put the eye into horizontal direction
    and make the eye in the same position
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    # calculate mid_point of two eyes
    mid = cal_mid((bb[0], bb[1]), (bb[2], bb[3]))
    width = bb[2] - bb[0]
    scale = width / dest_width  # same method to cal scale

    raw_width = dest_sz[0] * scale
    raw_height = dest_sz[1] * scale

    # crop the rotated image,the coodinate of middle of eyes is fixed
    crop_xy = (mid[0] - raw_width / 2.0, mid[1] - raw_height * extend)
    image = image.crop((int(crop_xy[0]), int(crop_xy[1]), int(crop_xy[0]+raw_width),
                        int(crop_xy[1]+raw_height)))
    # resize it
    image = image.resize(dest_sz, Image.ANTIALIAS)
    if is_gray:
        image = image.convert('L')
    return image

def crop_tf(im, result, is_gray=True, dest_sz=(85*2, 85*3)):
    if isinstance(im, np.ndarray):
        im = Image.fromarray(im)
    # calculate mid_point of two eyes
    mid_eye = cal_mid(result['left_eye'], result['right_eye'])

    # calculate the rotation angel
    eye_direction = (result['right_eye'][0] - result['left_eye'][0],
                     result['right_eye'][1] - result['left_eye'][1])
    rotation = math.atan2(float(eye_direction[1]), float(eye_direction[0]))

    left = mid_eye[0] - result['width']
    right = mid_eye[0] + result['width']
    up = int(mid_eye[1] - result['width']*1.5)
    down = int(mid_eye[1] + result['width']*1.5)

    crop_image = im.crop((left, up, right, down))
    crop_image = crop_image.resize(dest_sz)

    if is_gray:
        crop_image = crop_image.convert('L')
    crop_image = np.array(crop_image)

    return crop_image, rotation

if __name__ == '__main__':
    # import os
    # from detector import Detector
    # model_path = './model/mtcnn'
    # save_path = 'debug_crop'
    # if not os.path.exists(save_path):
    #     os.mkdir(save_path)
    # detector = Detector(model_path, gpu_fraction=0.5)
    #
    # origin_im = Image.open('test.jpg')
    # results = detector.detect_face(np.array(origin_im), debug=True)
    # for idx, result in enumerate(results):
    #     crop_im_list = crop_rotate_v3(origin_im, result)
    #     for idx_1, im in enumerate(crop_im_list):
    #         name = '{}_{}.jpg'.format(idx, idx_1)
    #         im.save(os.path.join(save_path, name))

    # import os
    # from naive_dlib import NaiveDlib
    # model_path = './model/dlib/shape_predictor_68_face_landmarks.dat'
    # save_path = 'debug_crop'
    # if not os.path.exists(save_path):
    #     os.mkdir(save_path)
    # detector = NaiveDlib(model_path)
    # origin_im = Image.open('test.jpg')
    # bbs = detector.getAllFaceBoundingBoxes(origin_im)
    # for idx, bb in enumerate(bbs):
    #     result = detector.interface(origin_im, bb)
    #     crop_im_list = crop_rotate_v3(origin_im, result)
    #     for idx_1, im in enumerate(crop_im_list):
    #         name = '{}_{}.jpg'.format(idx, idx_1)
    #         im.save(os.path.join(save_path, name))
    pass



