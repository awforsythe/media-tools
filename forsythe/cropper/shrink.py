import numpy as np

from forsythe.cropper.types import Edge, Corner


def line_white_percentage(mask, p0, p1):
    # Adapted from: https://stackoverflow.com/questions/32328179/opencv-3-0-python-lineiterator
    height, width = mask.shape[0], mask.shape[1]
    x0, y0 = int(p0[0]), int(p0[1])
    x1, y1 = int(p1[0]), int(p1[1])

    # Get the delta and absolute delta between the start and end points, so we can compute slope and relative location
    dx, dy = x1 - x0, y1 - y0
    dxa, dya = np.abs(dx), np.abs(dy)

    # Preallocate a buffer for our results, sized based on the distance between our sample points
    itbuffer = np.empty(shape=(np.maximum(dya, dxa), 2), dtype=np.int)
    itbuffer.fill(np.nan)

    # Use a form of Bresenham's algorithm to get sample coordinates along the line
    y_neg = y0 > y1
    x_neg = x0 > x1
    vertical = x0 == x1
    horizontal = not vertical and y0 == y1
    if vertical:
        itbuffer[:,0] = x0
        if y_neg:
            itbuffer[:,1] = np.arange(y0 - 1, y0 - dya - 1, -1)
        else:
            itbuffer[:,1] = np.arange(y0 + 1, y0 + dya + 1)
    elif horizontal:
        itbuffer[:,1] = y0
        if x_neg:
            itbuffer[:,0] = np.arange(x0 - 1, x0 - dxa - 1, -1)
        else:
            itbuffer[:,0] = np.arange(x0 + 1, x0 + dxa + 1)
    else:
        steep_slope = dya > dxa
        if steep_slope:
            slope = np.float32(dx) / np.float32(dy)
            if y_neg:
                itbuffer[:,1] = np.arange(y0 - 1, y0 - dya - 1, -1)
            else:
                itbuffer[:,1] = np.arange(y0 + 1, y0 + dya + 1)
            itbuffer[:,0] = (slope * (itbuffer[:,1] - y0)).astype(np.int) + x0
        else:
            slope = np.float32(dy) / np.float32(dx)
            if x_neg:
                itbuffer[:,0] = np.arange(x0 - 1, x0 - dxa - 1, -1)
            else:
                itbuffer[:,0] = np.arange(x0 + 1, x0 + dxa + 1)
            itbuffer[:,1] = (slope * (itbuffer[:,0] - x0)).astype(np.int) + y0

    # Remove coordinates that lie outside the bounds of the image
    x_col = itbuffer[:,0]
    y_col = itbuffer[:,1]
    itbuffer = itbuffer[(x_col >= 0) & (y_col >= 0) & (x_col < width) & (y_col < height)]

    # Sample the color values at each location in the input image
    value_sum = sum(mask[itbuffer[:,1].astype(np.uint), itbuffer[:,0].astype(np.uint)])
    return value_sum / (int(np.sqrt(dx * dx + dy * dy) * 255))


def get_direction(from_point, to_point):
    dx, dy = to_point[0] - from_point[0], to_point[1] - from_point[1]
    distance = np.sqrt(dx * dx + dy * dy)
    return (dx / distance, dy / distance)


def shrink_inside_mask(mask, corners, inset_interval, inset_white_threshold, extra_inset):
    to_right = get_direction(corners[Corner.top_left], corners[Corner.top_right])
    to_bottom = get_direction(corners[Corner.top_left], corners[Corner.bottom_left])

    v_add = lambda a, b: (a[0] + b[0], a[1] + b[1])
    v_mul = lambda a, x: (a[0] * x, a[1] * x)

    move_right = lambda p, dist: v_add(p, v_mul(to_right, dist))
    move_left = lambda p, dist: v_add(p, v_mul(to_right, -dist))
    move_down = lambda p, dist: v_add(p, v_mul(to_bottom, dist))
    move_up = lambda p, dist: v_add(p, v_mul(to_bottom, -dist))

    for edge, nudge_func in [
      (Edge.left, lambda p: move_right(p, inset_interval)),
      (Edge.right, lambda p: move_left(p, inset_interval)),
      (Edge.top, lambda p: move_down(p, inset_interval)),
      (Edge.bottom, lambda p: move_up(p, inset_interval)),
    ]:
        a, b = edge.corners
        while line_white_percentage(mask, corners[a], corners[b]) > inset_white_threshold:
            corners[a] = nudge_func(corners[a])
            corners[b] = nudge_func(corners[b])

    return {
        Corner.top_left: move_down(move_right(corners[Corner.top_left], extra_inset), extra_inset),
        Corner.top_right: move_down(move_left(corners[Corner.top_right], extra_inset), extra_inset),
        Corner.bottom_left: move_up(move_right(corners[Corner.bottom_left], extra_inset), extra_inset),
        Corner.bottom_right: move_up(move_left(corners[Corner.bottom_right], extra_inset), extra_inset),
    }
