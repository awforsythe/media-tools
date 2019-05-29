import cv2
import numpy as np

from forsythe.cropper.types import Corner


def crop_corners(img, size_factor):
    height, width = img.shape[0], img.shape[1]
    long_side = height if height > width else width
    short_side = width if height > width else height
    size = min(short_side // 2, max(1, int(long_side * size_factor)))
    return {
        Corner.top_left: img[:size, :size],
        Corner.top_right: img[:size, -size:],
        Corner.bottom_left: img[-size:, :size],
        Corner.bottom_right: img[-size:, -size:],
    }


def average_color(img):
    return img.mean(axis=0).mean(axis=0)


def bgr_to_hsv(bgr):
    return cv2.cvtColor(np.uint8([[bgr]]), cv2.COLOR_BGR2HSV)[0][0]


def get_key_color_from_corners(img_bgr, size_factor):
    corners = crop_corners(img_bgr, size_factor)
    corner_colors_bgr = [average_color(x) for x in corners.values()]
    corner_colors_hsv = [bgr_to_hsv(x) for x in corner_colors_bgr]
    return [int(x) for x in np.mean(corner_colors_hsv, axis=0)]


def get_color_mask(img_bgr, key_color_hsv, range_hsv):
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    range_lo_hsv = np.clip(np.subtract(key_color_hsv, range_hsv), 0, 255)
    range_hi_hsv = np.clip(np.add(key_color_hsv, range_hsv), 0, 255)
    return cv2.inRange(img_hsv, range_lo_hsv, range_hi_hsv)


def morph(op, mask, size):
    if size > 0:
        rect = cv2.getStructuringElement(cv2.MORPH_RECT, (size, size))
        return cv2.morphologyEx(mask, op, rect)
    return mask


def denoise(img_mask, erosion_size, dilation_size):
    eroded = morph(cv2.MORPH_CLOSE, img_mask, erosion_size)
    dilated = morph(cv2.MORPH_OPEN, eroded, dilation_size)
    return dilated


def get_background_mask(img_bgr, corner_size_factor, key_range_hsv, erosion_size, dilation_size):
    key_color_hsv = get_key_color_from_corners(img_bgr, corner_size_factor)
    mask = get_color_mask(img_bgr, key_color_hsv, key_range_hsv)
    return denoise(mask, erosion_size, dilation_size)
