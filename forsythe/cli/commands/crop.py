import os
import re

import cv2

from forsythe.cli.commands.common import CollectionCommand
from forsythe.files import collect_dirs_and_files, sort_files_by_ext, FileSequence
from forsythe.images.params import write_param, read_param, write_params, read_params
from forsythe.images.cache import get_cached_image_filepath, regenerate_cached_image

from forsythe.cropper.types import Corner
from forsythe.cropper.mask import get_background_mask
from forsythe.cropper.rect import find_rectilinear_corners
from forsythe.cropper.shrink import shrink_inside_mask


def draw_text(img, pos, text):
    x, y = pos
    cv2.putText(img, text, (x + 1, y + 1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)


def controls_label(i, label, img):
    y = 24 + (i * 20) + 2
    draw_text(img, (4, y), label)


def control(i, val_str, label, img, key):
    y = 24 + (i * 20)
    draw_text(img, (10, y), '%s (%s):' % (label, key))
    draw_text(img, (260, y), val_str)


def float_control(i, val, label, img, key):
    control(i, '%0.3f' % val, label, img, key)


def int_control(i, val, label, img, key):
    control(i, '%d' % val, label, img, key)


def is_key(code, key):
    key_code = ord(key)
    return code == key_code or code - 32 == key_code


class ConfigureCropCommand(CollectionCommand):

    @classmethod
    def init_parser(cls, parser):
        super().init_parser(parser)
        parser.add_argument('subdir', nargs='?', default='.')
        parser.add_argument('--image', '-i', type=int)

    @classmethod
    def run(cls, args):
        print('Collection: %s' % os.path.basename(args.collection))
        print('    Subdir: %s' % (args.subdir or '<ROOT>'))
        print('')

        images_dir = os.path.normpath(os.path.join(args.collection, args.subdir))
        _, filepaths = collect_dirs_and_files(images_dir)
        cr2_files = sort_files_by_ext(filepaths).get('.cr2', [])
        seq = FileSequence.load(cr2_files) if cr2_files else None
        if not seq:
            raise RuntimeError('No .cr2 image sequence found')

        cr2_filepath = seq.pattern % (args.image or seq.ranges[0][0])
        if not os.path.isfile(cr2_filepath):
            raise RuntimeError('No such file: %s' % cr2_filepath)
        cached_filepath = get_cached_image_filepath(cr2_filepath)
        if not os.path.isfile(cached_filepath):
            print('Generating cached image...')
            regenerate_cached_image(cr2_filepath)

        img = cv2.imread(cached_filepath)
        img = cv2.resize(img, (img.shape[1] // 4, img.shape[0] // 4))

        modes = ['original', 'color key', 'corners']
        mode_index = len(modes) - 1

        corner_size_factor = read_param(cr2_filepath, 'crop_corner_size_factor', 0.05)
        key_range_h = read_param(cr2_filepath, 'crop_key_range_h', 4.0)
        key_range_s = read_param(cr2_filepath, 'crop_key_range_s', 25.0)
        key_range_v = read_param(cr2_filepath, 'crop_key_range_v', 25.0)
        erosion_size = read_param(cr2_filepath, 'crop_erosion_size', 5)
        dilation_size = read_param(cr2_filepath, 'crop_dilation_size', 0)

        min_line_length_factor = read_param(cr2_filepath, 'crop_min_line_length_factor', 0.005)
        max_line_gap_factor = read_param(cr2_filepath, 'crop_max_line_gap_factor', 0.001)
        max_inclination_deg = read_param(cr2_filepath, 'crop_max_inclination_deg', 10.0)
        line_exclusion_size_factor = read_param(cr2_filepath, 'crop_line_exclusion_size_factor', 0.1)
        num_clusters = read_param(cr2_filepath, 'crop_num_clusters', 8)
        cluster_merge_threshold_size_factor = read_param(cr2_filepath, 'crop_cluster_merge_threshold_size_factor', 0.025)

        inset_interval = read_param(cr2_filepath, 'crop_inset_interval', 1.0)
        inset_white_threshold = read_param(cr2_filepath, 'crop_inset_white_threshold', 0.0025)
        extra_inset = read_param(cr2_filepath, 'crop_extra_inset', 8.0)

        save_prompted = False

        while True:
            mode = modes[mode_index]

            if mode_index >= modes.index('color key'):
                mask = get_background_mask(img, corner_size_factor, [key_range_h, key_range_s, key_range_v], erosion_size, dilation_size)

            if mode_index >= modes.index('corners'):
                rect_corners = find_rectilinear_corners(mask, min_line_length_factor, max_line_gap_factor, max_inclination_deg, line_exclusion_size_factor, num_clusters, cluster_merge_threshold_size_factor)
                corners = shrink_inside_mask(mask, rect_corners, inset_interval, inset_white_threshold, extra_inset * 0.25) if rect_corners else None

            base = None
            if mode == 'original':
                base = img.copy()
            elif mode == 'color key':
                base = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
            elif mode == 'corners':
                base = img.copy()
                if corners:
                    top_left = int(corners[Corner.top_left][0]), int(corners[Corner.top_left][1])
                    top_right = int(corners[Corner.top_right][0]), int(corners[Corner.top_right][1])
                    bottom_left = int(corners[Corner.bottom_left][0]), int(corners[Corner.bottom_left][1])
                    bottom_right = int(corners[Corner.bottom_right][0]), int(corners[Corner.bottom_right][1])
                    cv2.line(base, top_left, top_right, (255, 192, 192), 2)
                    cv2.line(base, top_right, bottom_right, (255, 192, 192), 2)
                    cv2.line(base, bottom_right, bottom_left, (255, 192, 192), 2)
                    cv2.line(base, bottom_left, top_left, (255, 192, 192), 2)
            else:
                raise RuntimeError('Unsupported mode: %s' % mode)


            height, width = base.shape[0], base.shape[1]
            long_side = height if height > width else width
            short_side = width if height > width else height
            size = min(short_side // 2, max(1, int(long_side * corner_size_factor)))
            cv2.rectangle(base, (0, 0), (size, size), (255, 192, 128), 1)
            cv2.rectangle(base, (base.shape[1] - size, 0), (base.shape[1], size), (255, 192, 128), 1)
            cv2.rectangle(base, (0, base.shape[0] - size), (size, base.shape[0]), (255, 192, 128), 1)
            cv2.rectangle(base, (base.shape[1] - size, base.shape[0] - size), (base.shape[1], base.shape[0]), (255, 192, 128), 1)

            mode_labels = [('[%s]' % m) if m == mode else m for m in modes]
            controls_label(0, 'MODE (,|.): %s' % ' | '.join(mode_labels), base)

            controls_label(2, 'COLOR KEY:', base)
            float_control(3, corner_size_factor, 'corner_size', base, 'C')
            float_control(4, key_range_h, 'key_range_h', base, 'H')
            float_control(5, key_range_s, 'key_range_s', base, 'S')
            float_control(6, key_range_v, 'key_range_v', base, 'V')
            int_control(7, erosion_size, 'erosion_size', base, 'E')
            int_control(8, dilation_size, 'dilation_size', base, 'D')

            controls_label(10, 'CORNERS:', base)
            float_control(11, min_line_length_factor, 'min_line_length_factor', base, 'L')
            float_control(12, max_line_gap_factor, 'max_line_gap_factor', base, 'G')
            float_control(13, max_inclination_deg, 'max_inclination_deg', base, 'I')
            float_control(14, line_exclusion_size_factor, 'line_exclusion_size_factor', base, 'X')
            int_control(15, num_clusters, 'num_clusters', base, 'N')
            float_control(16, cluster_merge_threshold_size_factor, 'cluster_merge_threshold', base, 'M')
            float_control(17, inset_interval, 'inset_interval', base, 'T')
            float_control(18, inset_white_threshold, 'inset_white_threshold', base, 'W')
            float_control(19, extra_inset, 'extra_inset', base, 'Z')

            if save_prompted:
                draw_text(base, (400, 400), 'Press ENTER to save settings for all images in collection.')
                draw_text(base, (500, 420), '(Press any other key to cancel.)')

            cv2.imshow('image', base)
            key = cv2.waitKeyEx(0)

            if key in (27, ord('q'), ord('Q')):
                break

            if key == 13:
                if save_prompted:
                    num_saved = 0
                    for num in seq.numbers:
                        filepath = seq.pattern % num
                        params = read_params(filepath)
                        params['crop_corner_size_factor'] = corner_size_factor
                        params['crop_key_range_h'] = key_range_h
                        params['crop_key_range_s'] = key_range_s
                        params['crop_key_range_v'] = key_range_v
                        params['crop_erosion_size'] = erosion_size
                        params['crop_dilation_size'] = dilation_size
                        params['crop_min_line_length_factor'] = min_line_length_factor
                        params['crop_max_line_gap_factor'] = max_line_gap_factor
                        params['crop_max_inclination_deg'] = max_inclination_deg
                        params['crop_line_exclusion_size_factor'] = line_exclusion_size_factor
                        params['crop_num_clusters'] = num_clusters
                        params['crop_cluster_merge_threshold_size_factor'] = cluster_merge_threshold_size_factor
                        params['crop_inset_interval'] = inset_interval
                        params['crop_inset_white_threshold'] = inset_white_threshold
                        params['crop_extra_inset'] = extra_inset
                        write_params(filepath, params)
                        num_saved += 1
                    print('Wrote crop params for %d images.' % num_saved)
                    save_prompted = False
                else:
                    save_prompted = True
            else:
                save_prompted = False

            if key == ord(','):
                mode_index = (mode_index - 1) if mode_index > 0 else len(modes) - 1
            elif key == ord('.'):
                mode_index = (mode_index + 1) % len(modes)
            elif is_key(key, 'C'):
                incr = 0.01 if key == ord('c') else -0.01
                corner_size_factor += incr
            elif is_key(key, 'H'):
                incr = 0.1 if key == ord('h') else -0.1
                key_range_h += incr
            elif is_key(key, 'S'):
                incr = 0.1 if key == ord('s') else -0.1
                key_range_s += incr
            elif is_key(key, 'V'):
                incr = 0.1 if key == ord('v') else -0.1
                key_range_v += incr
            elif is_key(key, 'E'):
                incr = 1 if key == ord('e') else -1
                erosion_size += incr
            elif is_key(key, 'D'):
                incr = 1 if key == ord('d') else -1
                dilation_size += incr
            elif is_key(key, 'L'):
                incr = (1.0 if key == ord('l') else -1.0) * 0.001
                min_line_length_factor += incr
            elif is_key(key, 'G'):
                incr = (1.0 if key == ord('g') else -1.0) * 0.0001
                max_line_gap_factor += incr
            elif is_key(key, 'I'):
                incr = (1.0 if key == ord('i') else -1.0) * 1.0
                max_inclination_deg += incr
            elif is_key(key, 'X'):
                incr = (1.0 if key == ord('x') else -1.0) * 0.1
                line_exclusion_size_factor += incr
            elif is_key(key, 'N'):
                incr = (1 if key == ord('n') else -1)
                num_clusters += incr
            elif is_key(key, 'M'):
                incr = (1.0 if key == ord('m') else -1.0) * 0.025
                cluster_merge_threshold_size_factor += incr
            elif is_key(key, 'T'):
                incr = (1.0 if key == ord('t') else -1.0) * 0.1
                inset_interval += incr
            elif is_key(key, 'W'):
                incr = (1.0 if key == ord('w') else -1.0) * 0.001
                inset_white_threshold += incr
            elif is_key(key, 'Z'):
                incr = (1.0 if key == ord('z') else -1.0)
                extra_inset += incr

        cv2.destroyAllWindows()
