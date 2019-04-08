"""
this script is use landmark to do similiar transform for detected face
"""
from PIL import Image
import math
import numpy as np


def Distance(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx*dx+dy*dy)


def cal_mid(p1, p2):
    m_x = (p2[0] + p1[0]) / 2.0
    m_y = (p2[1] + p1[1]) / 2.0
    return m_x, m_y


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


def crop_rotate_v2(image,bbox,eye_left, eye_right, bb_width, is_gray=True,
                   dest_width=85, extend=0.3, dest_sz=(96, 112)):
    """
    this function is used to do similarity transformation,
    put the eye into horizontal direction
    and make the eye in the same position
    """

    # calculate mid_point of two eyes
    mid_eye = cal_mid(eye_left, eye_right)
    scale = bb_width / dest_width  # the width of bbox keeps unchange

    top = max(0, int(mid_eye[1] - bbox.height()*1.5))
    bottom = min(image.shape[0] - 1, int(mid_eye[1] + bbox.height()*1.5))
    left = max(0, int(mid_eye[0] - bbox.width()*1.5))
    right = min(image.shape[1] - 1, int(mid_eye[0] + bbox.width()*1.5))
    # crop_image = image[int(mid_eye[1]-bbox.height()):int(mid_eye[1]+bbox.height()),
    #              int(mid_eye[0] - bbox.width()):int(mid_eye[0] + bbox.width())]
    crop_image = image[top:bottom, left:right]

    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)

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
    return image,crop_image


def crop_only(image, bb, dest_width=85, extend=0.4,
              is_gray=True, dest_sz=(96, 112)):
    """
    bbox should be left up right bottom
    this function is used to do similarity transformation,
    put the eye into horizontal direction
    and make the eye in the same position
    """
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
    image = np.array(image)
    return image


