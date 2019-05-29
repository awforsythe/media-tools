import cv2

from forsythe.cropper.mask import get_background_mask
from forsythe.cropper.rect import find_rectilinear_corners
from forsythe.cropper.shrink import shrink_inside_mask
from forsythe.cropper.output import get_crop_params, rotate_crop_params
from forsythe.cropper.types import Corner, Edge

CORNER_SIZE_FACTOR = 0.05
KEY_RANGE_HSV = [5.0, 20.0, 20.0]
EROSION_SIZE = 5
DILATION_SIZE = 0

MIN_LINE_LENGTH_FACTOR = 0.005
MAX_LINE_GAP_FACTOR = 0.001
MAX_INCLINATION_DEG = 10.0
LINE_EXCLUSION_SIZE_FACTOR = 0.1
NUM_CLUSTERS = 8
CLUSTER_MERGE_THRESHOLD_SIZE_FACTOR = 0.025

INSET_INTERVAL = 1.0
INSET_WHITE_THRESHOLD = 0.0025
EXTRA_INSET = 8.0


def compute_crop_params(image_filepath, top_edge_name=None):
    top_edge = Edge[top_edge_name] if top_edge_name else Edge.top

    img = cv2.imread(image_filepath)
    mask = get_background_mask(img, CORNER_SIZE_FACTOR, KEY_RANGE_HSV, EROSION_SIZE, DILATION_SIZE)
    rect_corners = find_rectilinear_corners(mask, MIN_LINE_LENGTH_FACTOR, MAX_LINE_GAP_FACTOR, MAX_INCLINATION_DEG, LINE_EXCLUSION_SIZE_FACTOR, NUM_CLUSTERS, CLUSTER_MERGE_THRESHOLD_SIZE_FACTOR)
    corners = shrink_inside_mask(mask, rect_corners, INSET_INTERVAL, INSET_WHITE_THRESHOLD, EXTRA_INSET)
    params = get_crop_params(img, corners)
    return rotate_crop_params(params, top_edge)
