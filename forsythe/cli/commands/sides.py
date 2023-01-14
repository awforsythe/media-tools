import os
import shutil

import cv2
import numpy as np

from forsythe.cli.commands.common import CollectionCommand
from forsythe.files import collect_dirs_and_files, sort_files_by_ext, temporary_directory, FileSequence
from forsythe.images.params import read_params, write_param
from forsythe.images.cache import generate_cache, image_iterator
from forsythe.cropper.mask import get_background_mask
from forsythe.cropper import CORNER_SIZE_FACTOR, KEY_RANGE_HSV, EROSION_SIZE, DILATION_SIZE


class TagSidesCommand(CollectionCommand):

    @classmethod
    def init_parser(cls, parser):
        super().init_parser(parser)
        parser.add_argument('subdir', nargs='?', default='.')
        parser.add_argument('--threshold', '-t', type=float, default=0.02)

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

        print('Generating image cache...')
        generate_cache(images_dir)

        tmp_dirpath = os.path.join(images_dir, '.temp-sides')
        with temporary_directory(tmp_dirpath):

            os.startfile(tmp_dirpath)

            backs_dirpath = os.path.join(tmp_dirpath, 'backs')
            os.makedirs(backs_dirpath)

            cr2_filepath_lookup = {}
            for image_filepath, cached_filepath in image_iterator(images_dir):
                short_filename = os.path.basename(cached_filepath)
                cr2_filepath_lookup[short_filename] = image_filepath

                img = cv2.imread(cached_filepath)
                img = cv2.resize(img, (img.shape[1] // 4, img.shape[0] // 4))

                is_back = None
                image_params = read_params(image_filepath)
                if image_params.get('side') in ('front', 'back'):
                    is_back = image_params.get('side') == 'back'
                    print('%s -- loaded -- %s' % (short_filename, 'back' if is_back else 'FRONT'))

                if is_back is None:
                    corner_size_factor = image_params.get('crop_corner_size_factor', CORNER_SIZE_FACTOR)
                    key_range_h = image_params.get('crop_key_range_h', KEY_RANGE_HSV[0])
                    key_range_s = image_params.get('crop_key_range_S', KEY_RANGE_HSV[1])
                    key_range_v = image_params.get('crop_key_range_v', KEY_RANGE_HSV[2])
                    erosion_size = image_params.get('crop_erosion_size', EROSION_SIZE)
                    dilation_size = image_params.get('crop_dilation_size', DILATION_SIZE)
                    mask = get_background_mask(img, corner_size_factor, [key_range_h, key_range_s, key_range_v], erosion_size, dilation_size)
                    alpha = cv2.erode(~mask, np.ones((5, 5), np.uint8), iterations=5)

                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    res = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 7, 5.0)
                    res = cv2.bitwise_and(res, res, mask=alpha)
                    percentage = np.count_nonzero(res) / np.count_nonzero(alpha)

                    is_back = percentage < args.threshold
                    print('%s -- % 5.1f%% -- %s' % (short_filename, percentage * 100.0, 'back' if is_back else 'FRONT'))

                dst_dirpath = backs_dirpath if is_back else tmp_dirpath
                dst_filepath = os.path.join(dst_dirpath, short_filename)
                cv2.imwrite(dst_filepath, img)

            print('')
            print('Please check the .temp-sides directory and move any back images to backs folder.')
            print('Then check the backs folder and make sure it doesn\'t contain any front images.')
            input('Once all images are sorted, press enter to proceed.')

            for filename in os.listdir(tmp_dirpath):
                cr2_filepath = cr2_filepath_lookup.get(filename)
                if cr2_filepath:
                    print('%s - front' % filename)
                    write_param(cr2_filepath, 'side', 'front')

            for filename in os.listdir(backs_dirpath):
                cr2_filepath = cr2_filepath_lookup.get(filename)
                if cr2_filepath:
                    print('%s - back' % filename)
                    write_param(cr2_filepath, 'side', 'back')


class MatchSidesCommand(CollectionCommand):

    @classmethod
    def init_parser(cls, parser):
        super().init_parser(parser)
        parser.add_argument('subdir', nargs='?', default='.')

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

        print('Generating image cache...')
        generate_cache(images_dir)

        fronts = []
        backs = []

        '''
        for image_filepath, cached_filepath in reversed(list(image_iterator(images_dir))):
            name = os.path.splitext(os.path.basename(image_filepath))[0]
            image_params = read_params(image_filepath)
            side = image_params.get('side')
            if side is None or side not in ('front', 'back'):
                raise RuntimeError('%s is not tagged front or back! Use fma tag-sides to tag all images.' % os.path.basename(image_filepath))
            if side == 'front':
                fronts.append((image_filepath, cached_filepath))
                if len(fronts) != len(backs):
                    backs.append(None)
            else:
                backs.append((image_filepath, cached_filepath))
        '''

        prev_side = 'back'
        for image_filepath, cached_filepath in reversed(list(image_iterator(images_dir))):
            image_params = read_params(image_filepath)
            side = image_params.get('side')
            if side is None or side not in ('front', 'back'):
                raise RuntimeError('%s is not tagged front or back! Use fma tag-sides to tag all images.' % os.path.basename(image_filepath))
            if side == 'front':
                fronts.append((image_filepath, cached_filepath))
                if len(fronts) != len(backs):
                    backs.append(None)
            else:
                backs.append((image_filepath, cached_filepath))
                if len(fronts) != len(backs) - 1:
                    fronts.append(None)
            prev_side = side

        fronts = [x for x in reversed(fronts) if x]
        backs.reverse()

        i = 0
        img_width = 200
        img_height = 200
        back_scale = 0.75
        commit_prompted = False
        commit_changes = False
        while True:
            n = max(len(fronts), len(backs))

            if i < len(fronts):
                img_front = cv2.imread(fronts[i][1])
                img_width = img_front.shape[1] // 6
                img_height = img_front.shape[0] // 6
                img_front = cv2.resize(img_front, (img_width, img_height))

            vpad = 80
            canvas_width = img_width + int(img_width * back_scale)
            canvas_height = img_height + (vpad * 2)
            canvas = np.zeros((canvas_height, canvas_width, 3), np.uint8)

            if i < len(fronts):
                canvas[vpad:vpad+img_height, 0:img_width] = img_front

            if i < len(backs) and backs[i] is not None:
                back_width = int(img_width * back_scale)
                back_height = int(img_height * back_scale)
                img_back = cv2.imread(backs[i][1])
                img_back = cv2.resize(img_back, (back_width, back_height))
                canvas[vpad:vpad+back_height, img_width:img_width+back_width] = img_back

            cellpad = 3.0
            total_cellpad = cellpad * n + cellpad + cellpad
            cell_width = (float(canvas_width) - total_cellpad) / n
            cell_height = 20.0
            bot_cell_y = canvas_height - cellpad - cell_height
            top_cell_y = bot_cell_y - cellpad - cell_height
            cell_x = cellpad
            for j in range(n):
                is_current = j == i

                if j < len(fronts):
                    top_color = [220, 96, 96] if is_current else [96, 64, 64]
                    cv2.rectangle(canvas, (int(cell_x), int(top_cell_y)), (int(cell_x + cell_width), int(top_cell_y + cell_height)), top_color, -1)

                if j < len(backs):
                    thickness = 1 if backs[j] is None else -1
                    bot_color = [96, 220, 96] if is_current else [64, 96, 64]
                    cv2.rectangle(canvas, (int(cell_x), int(bot_cell_y)), (int(cell_x + cell_width), int(bot_cell_y + cell_height)), bot_color, thickness)
                cell_x += cell_width + cellpad

            if commit_prompted:
                msg = 'Press ENTER again to exit and save changes. Press any other key to cancel.'
                cv2.putText(canvas, msg, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            if i < len(fronts):
                cv2.putText(canvas, os.path.basename(fronts[i][0]), (20, vpad - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            if i < len(backs) and backs[i] is not None:
                cv2.putText(canvas, os.path.basename(backs[i][0]), (20 + img_width, vpad - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            cv2.imshow('image', canvas)
            key = cv2.waitKeyEx(0)

            if key in (27, ord('q'), ord('Q')):
                break

            if key == 13:
                if commit_prompted:
                    commit_changes = True
                    break
                else:
                    commit_prompted = True
            else:
                commit_prompted = False

            KEY_UP = 2490368
            KEY_DOWN = 2621440
            KEY_RIGHT = 2555904
            KEY_LEFT = 2424832
            KEY_DELETE = 3014656

            if key == KEY_RIGHT or key == 32:
                i = min(n - 1, i + 1)
            elif key == KEY_LEFT:
                i = max(0, i - 1)
            elif key == KEY_DOWN:
                i = min(n - 1, i + 10)
            elif key == KEY_UP:
                i = max(0, i - 10)
            elif key == KEY_DELETE:
                if i < len(backs):
                    if backs[i] is None:
                        backs.pop(i)
                    else:
                        backs.insert(i, None)

        if commit_changes:
            print('Committing matches...')
            for i in range(len(backs)):
                if backs[i] is not None and i < len(fronts):
                    front_image = fronts[i][0]
                    back_image = backs[i][0]
                    write_param(front_image, 'reverse', os.path.basename(back_image))
        else:
            print('No changes saved.')

