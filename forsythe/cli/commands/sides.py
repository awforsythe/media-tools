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
