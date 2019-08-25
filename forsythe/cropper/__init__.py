import cv2

from forsythe.cropper.mask import get_background_mask
from forsythe.cropper.rect import find_rectilinear_corners
from forsythe.cropper.shrink import shrink_inside_mask
from forsythe.cropper.output import get_crop_params, rotate_crop_params
from forsythe.cropper.types import Corner, Edge

CORNER_SIZE_FACTOR = 0.05
KEY_RANGE_HSV = [5.0, 25.0, 25.0]
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

    corner_size_factor = read_param(image_filepath, 'crop_corner_size_factor', CORNER_SIZE_FACTOR)
    key_range_h = read_param(image_filepath, 'crop_key_range_h', KEY_RANGE_HSV[0])
    key_range_s = read_param(image_filepath, 'crop_key_range_s', KEY_RANGE_HSV[1])
    key_range_v = read_param(image_filepath, 'crop_key_range_v', KEY_RANGE_HSV[2])
    erosion_size = read_param(image_filepath, 'crop_erosion_size', EROSION_SIZE)
    dilation_size = read_param(image_filepath, 'crop_dilation_size', DILATION_SIZE)

    min_line_length_factor = read_param(image_filepath, 'crop_min_line_length_factor', MIN_LINE_LENGTH_FACTOR)
    max_line_gap_factor = read_param(image_filepath, 'crop_max_line_gap_factor', MAX_LINE_GAP_FACTOR)
    max_inclination_deg = read_param(image_filepath, 'crop_max_inclination_deg', MAX_INCLINATION_DEG)
    line_exclusion_size_factor = read_param(image_filepath, 'crop_line_exclusion_size_factor', LINE_EXCLUSION_SIZE_FACTOR)
    num_clusters = read_param(image_filepath, 'crop_num_clusters', NUM_CLUSTERS)
    cluster_merge_threshold_size_factor = read_param(image_filepath, 'crop_cluster_merge_threshold_size_factor', CLUSTER_MERGE_THRESHOLD_SIZE_FACTOR)

    inset_interval = read_param(image_filepath, 'crop_inset_interval', INSET_INTERVAL)
    inset_white_threshold = read_param(image_filepath, 'crop_inset_white_threshold', INSET_WHITE_THRESHOLD)
    extra_inset = read_param(image_filepath, 'crop_extra_inset', EXTRA_INSET)

    img = cv2.imread(image_filepath)
    mask = get_background_mask(img, corner_size_factor, [key_range_h, key_range_s, key_range_v], erosion_size, dilation_size)
    rect_corners = find_rectilinear_corners(mask, min_line_length_factor, max_line_gap_factor, max_inclination_deg, line_exclusion_size_factor, num_clusters, cluster_merge_threshold_size_factor)
    if not rect_corners:
        return None

    corners = shrink_inside_mask(mask, rect_corners, inset_interval, inset_white_threshold, extra_inset)
    params = get_crop_params(img, corners)
    return rotate_crop_params(params, top_edge)
