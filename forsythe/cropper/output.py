import math
import numpy as np

from forsythe.cropper.types import Corner, Edge


def v_add(p0, p1):
    (x0, y0), (x1, y1) = p0, p1
    return (x0 + x1, y0 + y1)


def v_sub(p0, p1):
    (x0, y0), (x1, y1) = p0, p1
    return (x0 - x1, y0 - y1)


def v_mul(p0, scalar):
    x0, y0 = p0
    return (x0 * scalar, y0 * scalar)


def v_div(p0, scalar):
    x0, y0 = p0
    return (x0 / scalar, y0 / scalar)


def v_mag(p0):
    x0, y0 = p0
    return np.sqrt(x0 * x0 + y0 * y0)


def v_mid(p0, p1):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    return (x0 + dx * 0.5, y0 + dy * 0.5)


def v_dist(p0, p1):
    disp = v_sub(p1, p0)
    mag = v_mag(disp)
    if mag != 0.0:
        return v_div(disp, mag)
    return 0.0


def v_angle(p0, p1):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    return math.atan2(dy, dx)


def v_rotate(p0, theta, origin=None):
    c, s = np.cos(theta), np.sin(theta)
    tmp_x, tmp_y = v_sub(p0, origin) if origin else p0
    result = (tmp_x * c - tmp_y * s, tmp_x * s + tmp_y * c)
    return v_add(result, origin) if origin else result


def aabb_size(points):
    x_min, x_max = None, None
    y_min, y_max = None, None
    for x0, y0 in points:
        if x_min is None or x0 < x_min:
            x_min = x0
        if x_max is None or x0 > x_max:
            x_max = x0
        if y_min is None or y0 < y_min:
            y_min = y0
        if y_max is None or y0 > y_max:
            y_max = y0
    return (x_max - x_min, y_max - y_min)


def get_crop_params(img, corners):
    crop_width = v_dist(corners[Corner.top_left], corners[Corner.top_right])
    crop_height = v_dist(corners[Corner.top_left], corners[Corner.bottom_left])
    crop_center = v_mid(corners[Corner.top_left], corners[Corner.bottom_right])

    angle = -v_angle(corners[Corner.top_left], corners[Corner.top_right])

    image_height, image_width = img.shape[0], img.shape[1]
    image_center = (image_width * 0.5, image_height * 0.5)
    image_corners = {
        Corner.top_left: (0.0, 0.0),
        Corner.top_right: (float(image_width), 0.0),
        Corner.bottom_left: (0.0, float(image_height)),
        Corner.bottom_right: (float(image_width), float(image_height)),
    }
    rotated_image_corners = {corner: v_rotate(p0, angle, image_center) for corner, p0 in image_corners.items()}
    rotated_size = aabb_size(rotated_image_corners.values())
    rotation_expansion = v_sub(rotated_size, (image_width, image_height))

    rotated_top_left = v_add(v_rotate(corners[Corner.top_left], angle, image_center), v_mul(rotation_expansion, 0.5))
    rotated_bottom_right = v_add(v_rotate(corners[Corner.bottom_right], angle, image_center), v_mul(rotation_expansion, 0.5))

    angle_deg = np.degrees(angle)
    cx = rotated_top_left[0] / rotated_size[0]
    cy = rotated_top_left[1] / rotated_size[1]
    cw = rotated_bottom_right[0] / rotated_size[0]
    ch = rotated_bottom_right[1] / rotated_size[1]

    return {
        'angle': angle_deg,
        'cx': cx,
        'cy': cy,
        'cw': cw,
        'ch': ch,
    }


def rotate_crop_params(params, top_edge):
    return {
        Edge.top: params,
        Edge.bottom: {
            'angle': params['angle'] + 180.0,
            'cx': 1.0 - params['cw'],
            'cy': 1.0 - params['ch'],
            'cw': 1.0 - params['cx'],
            'ch': 1.0 - params['cy'],
        },
        Edge.left: {
            'angle': params['angle'] + 90.0,
            'cx': 1.0 - params['ch'],
            'cy': params['cx'],
            'cw': 1.0 - params['cy'],
            'ch': params['cw'],
        },
        Edge.right: {
            'angle': params['angle'] - 90.0,
            'cx': params['cy'],
            'cy': 1.0 - params['cw'],
            'cw': params['ch'],
            'ch': 1.0 - params['cx'],
        },
    }[top_edge]
