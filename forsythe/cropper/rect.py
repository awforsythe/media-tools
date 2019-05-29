import math
from collections import defaultdict

import cv2
import numpy as np

from forsythe.cropper.types import Corner, Edge


def get_midpoint(p0, p1):
    x0, y0 = p0
    x1, y1 = p1
    return (x0 + (x1 - x0) * 0.5, y1 + (y1 - y0) * 0.5)


def get_lines(lines_result):
    lines = []
    for result in lines_result:
        assert len(result) == 1
        x0, y0, x1, y1 = result[0]
        lines.append(((x0, y0), (x1, y1)))
    return lines


def sort_lines_by_edge(lines):
    midpoints = [get_midpoint(p0, p1) for p0, p1 in lines]
    center = np.mean(midpoints, axis=0)

    results = {edge: [] for edge in Edge.__members__.values()}
    for line, midpoint in zip(lines, midpoints):
        (x0, y0), (x1, y1) = line
        dx, dy = x1 - x0, y1 - y0
        if abs(dx) > abs(dy):
            if midpoint[1] < center[1]:
                results[Edge.top].append(line)
            else:
                results[Edge.bottom].append(line)
        else:
            if midpoint[0] < center[0]:
                results[Edge.left].append(line)
            else:
                results[Edge.right].append(line)
    return results


def find_vertical_and_horizontal(lines, max_inclination_deg, vertical_exclusion_x_range, horizontal_exclusion_y_range):
    vertical = []
    horizontal = []
    for line, midpoint in zip(lines, [get_midpoint(p0, p1) for p0, p1 in lines]):
        (x0, y0), (x1, y1) = line
        dx, dy = x1 - x0, y1 - y0
        inclination_deg = abs(np.degrees(math.atan2(dy, dx)))
        if inclination_deg <= max_inclination_deg or inclination_deg >= (180.0 - max_inclination_deg):
            if midpoint[1] < horizontal_exclusion_y_range[0] or midpoint[1] > horizontal_exclusion_y_range[1]:
                horizontal.append(line)
        elif inclination_deg >= (90.0 - max_inclination_deg) and inclination_deg <= (90.0 + max_inclination_deg):
            if midpoint[0] < vertical_exclusion_x_range[0] or midpoint[0] > vertical_exclusion_x_range[1]:
                vertical.append(line)
    return vertical, horizontal


def find_clusters(lines, coord, num_clusters, merge_threshold):

    class Cluster(object):
        def __init__(self):
            self.centers = []
            self.labels = set()
            self.count = 0

        @property
        def mean_center(self):
            return np.mean(self.centers)

        def add(self, center, label, count):
            self.centers.append(center)
            self.labels.add(label)
            self.count += count

        def should_merge(self, other_center, distance_threshold):
            return abs(other_center - self.mean_center) <= distance_threshold

    midpoints = np.array([get_midpoint(p0, p1) for p0, p1 in lines])
    data = np.float32(midpoints[:,coord])

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    flags = cv2.KMEANS_RANDOM_CENTERS
    _, labels, centers = cv2.kmeans(data, num_clusters, None, criteria, 10, flags)

    counts = defaultdict(int)
    for label in labels:
        counts[label[0]] += 1

    clusters = []
    for label, count in sorted(counts.items(), key=lambda v: -v[1]):
        center = centers[label][0]
        cluster = next((c for c in clusters if c.should_merge(center, merge_threshold)), None)
        if not cluster:
            cluster = Cluster()
            clusters.append(cluster)
        cluster.add(center, label, count)

    clusters.sort(key=lambda c: -c.count)
    if clusters[0].mean_center < clusters[1].mean_center:
        min_cluster, max_cluster = clusters[:2]
    else:
        max_cluster, min_cluster = clusters[:2]

    min_lines = []
    max_lines = []
    for i, label in enumerate(labels):
        label = label[0]
        if label in min_cluster.labels:
            min_lines.append(lines[i])
        elif label in max_cluster.labels:
            max_lines.append(lines[i])

    return min_lines, max_lines


def get_extremes(lines, coord):
    min_line_coord = None
    min_line = None
    max_line_coord = None
    max_line = None
    for line in lines:
        for point in line:
            if min_line_coord is None or point[coord] < min_line_coord:
                min_line_coord = point[coord]
                min_line = line
            if max_line_coord is None or point[coord] > max_line_coord:
                max_line_coord = point[coord]
                max_line = line
    return min_line, max_line


def find_edge_lines(mask, min_length_size_factor, max_gap_size_factor, max_inclination_deg, line_exclusion_size_factor, num_clusters, cluster_merge_threshold_size_factor):
    height, width = mask.shape[0], mask.shape[1]
    long_side = max(height, width)

    min_line_length = max(1, long_side * min_length_size_factor)
    max_line_gap = max(1, long_side * max_gap_size_factor)
    edges = cv2.Canny(mask, 50, 150)
    lines = get_lines(cv2.HoughLinesP(edges, 1, np.pi / 180.0, 15, np.array([]), min_line_length, max_line_gap))

    exclusion_extent = long_side * line_exclusion_size_factor * 0.5
    vertical_exclusion_x_range = (width // 2 - exclusion_extent, width // 2 + exclusion_extent)
    horizontal_exclusion_y_range = (height // 2 - exclusion_extent, height // 2 + exclusion_extent)
    vertical, horizontal = find_vertical_and_horizontal(lines, max_inclination_deg, vertical_exclusion_x_range, horizontal_exclusion_y_range)

    cluster_merge_threshold = long_side * cluster_merge_threshold_size_factor
    left_lines, right_lines = find_clusters(vertical, 0, num_clusters, cluster_merge_threshold)
    top_lines, bottom_lines = find_clusters(horizontal, 1, num_clusters, cluster_merge_threshold)

    return {
        Edge.left: left_lines,
        Edge.right: right_lines,
        Edge.top: top_lines,
        Edge.bottom: bottom_lines,
    }


def line_intersection(line_a, line_b):
    p0, p1 = line_a
    p2, p3 = line_b

    x_num = (p0[0] * p1[1] - p0[1] * p1[0]) * (p2[0] - p3[0]) - (p0[0] - p1[0]) * (p2[0] * p3[1] - p2[1] * p3[0])
    x_denom = (p0[0] - p1[0]) * (p2[1] - p3[1]) - (p0[1] - p1[1]) * (p2[0] - p3[0])

    y_num = (p0[0] * p1[1] - p0[1] * p1[0]) * (p2[1] - p3[1]) - (p0[1] - p1[1]) * (p2[0] * p3[1] - p2[1] * p3[0])
    y_denom = (p0[0] - p1[0]) * (p2[1] - p3[1]) - (p0[1] - p1[1]) * (p2[0] - p3[0])

    return (int(x_num / x_denom), int(y_num / y_denom))


def find_corners(mask, min_length_size_factor, max_gap_size_factor, max_inclination_deg, line_exclusion_size_factor, num_clusters, cluster_merge_threshold_size_factor):
    edge_lines = find_edge_lines(mask, min_length_size_factor, max_gap_size_factor, max_inclination_deg, line_exclusion_size_factor, num_clusters, cluster_merge_threshold_size_factor)

    top_leftmost, top_rightmost = get_extremes(edge_lines[Edge.top], 0)
    bottom_leftmost, bottom_rightmost = get_extremes(edge_lines[Edge.bottom], 0)
    left_topmost, left_bottommost = get_extremes(edge_lines[Edge.left], 1)
    right_topmost, right_bottommost = get_extremes(edge_lines[Edge.right], 1)

    return {
        Corner.top_left: line_intersection(top_leftmost, left_topmost),
        Corner.top_right: line_intersection(top_rightmost, right_topmost),
        Corner.bottom_left: line_intersection(bottom_leftmost, left_bottommost),
        Corner.bottom_right: line_intersection(bottom_rightmost, right_bottommost),
    }


def dist(p0, p1):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    return math.sqrt(dx * dx + dy * dy)


def find_shortest_edge(edges):
    min_length = None
    min_length_edge = None
    for edge, (p0, p1) in edges.items():
        length = dist(p0, p1)
        if min_length is None or length < min_length:
            min_length = length
            min_length_edge = edge
    return min_length_edge


def get_angle_from_vertical(line):
    (x0, y0), (x1, y1) = line
    dx, dy = x1 - x0, y1 - y0
    return math.atan2(dy, dx)


def get_angle_from_horizontal(line):
    (x0, y0), (x1, y1) = line
    dx, dy = x1 - x0, y1 - y0
    return math.atan2(dy, dx) - (math.pi / 2.0)


def rotate(p, theta):
    c, s = np.cos(theta), np.sin(theta)
    m = np.matrix([[c, -s], [s, c]])
    return tuple((p * m).tolist()[0])


def find_rectilinear_corners(mask, min_length_size_factor, max_gap_size_factor, max_inclination_deg, line_exclusion_size_factor, num_clusters, cluster_merge_threshold_size_factor):
    corners = find_corners(mask, min_length_size_factor, max_gap_size_factor, max_inclination_deg, line_exclusion_size_factor, num_clusters, cluster_merge_threshold_size_factor)
    edges = {
        Edge.left: (corners[Corner.top_left], corners[Corner.bottom_left]),
        Edge.right: (corners[Corner.top_right], corners[Corner.bottom_right]),
        Edge.top: (corners[Corner.top_left], corners[Corner.top_right]),
        Edge.bottom: (corners[Corner.bottom_left], corners[Corner.bottom_right]),
    }

    shortest_edge = find_shortest_edge(edges)
    if shortest_edge.vertical:
        theta = get_angle_from_vertical(edges[shortest_edge])
    else:
        theta = get_angle_from_horizontal(edges[shortest_edge])

    rot_corners = {corner: rotate(p0, theta) for corner, p0 in corners.items()}

    leftmost_x = lambda p0, p1: p0[0] if p0[0] < p1[0] else p1[0]
    rightmost_x = lambda p0, p1: p0[0] if p0[0] > p1[0] else p1[0]
    topmost_y = lambda p0, p1: p0[1] if p0[1] < p1[1] else p1[1]
    bottommost_y = lambda p0, p1: p0[1] if p0[1] > p1[1] else p1[1]

    left_x = rightmost_x(rot_corners[Corner.top_left], rot_corners[Corner.bottom_left])
    right_x = leftmost_x(rot_corners[Corner.top_right], rot_corners[Corner.bottom_right])
    top_y = bottommost_y(rot_corners[Corner.top_left], rot_corners[Corner.top_right])
    bottom_y = topmost_y(rot_corners[Corner.bottom_left], rot_corners[Corner.bottom_right])

    return {
        Corner.top_left: rotate((left_x, top_y), -theta),
        Corner.top_right: rotate((right_x, top_y), -theta),
        Corner.bottom_left: rotate((left_x, bottom_y), -theta),
        Corner.bottom_right: rotate((right_x, bottom_y), -theta),
    }
