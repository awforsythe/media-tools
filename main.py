import os
import argparse
import multiprocessing
import cv2

from forsythe.images.cache import generate_cache, image_iterator
from forsythe.images.params import write_param, read_param

from forsythe.darktable.process import regenerate_xmps, run_darktable
from forsythe.darktable.iop import dt_iop_clipping_params_t, dt_iop_exposure_params_t
from forsythe.darktable.xmp import edit_xmp

from forsythe.cropper import compute_crop_params


def temp_orient_gui(img):
    height, width = img.shape[:2]
    new_height = 1280
    new_width = int((height / width) * new_height)

    cv2.imshow('image', cv2.resize(img, (new_height, new_width)) if height > new_height else img)
    key = cv2.waitKeyEx(0)
    cv2.destroyAllWindows()

    return {
        2490368: 'top',
        2621440: 'bottom',
        2424832: 'left',
        2555904: 'right',
    }.get(key)


def run_orient(args):
    print('Generating image cache...')
    generate_cache(args.directory)

    items = list(image_iterator(args.directory))
    i = 0
    while i < len(items):
        image_filepath, cached_filepath = items[i]
        img = cv2.imread(cached_filepath)
        top_edge = temp_orient_gui(img)
        if top_edge:
            write_param(image_filepath, 'top_edge', top_edge)
            print('%s --> %s' % (image_filepath, top_edge))
            i += 1
        else:
            i -= 1
            print('Back to %s.' % items[i][0])


def run_crop(args):
    print('Regenerating .xmp sidecar files...')
    regenerate_xmps(args.directory)

    for image_filepath, cached_filepath in image_iterator(args.directory):
        top_edge = read_param(image_filepath, 'top_edge', 'top')
        ev_delta = 0.4

        try:
            crop_params = compute_crop_params(cached_filepath, top_edge)
            print ('%s -> %r' % (os.path.basename(image_filepath), crop_params))

            iop_clipping = dt_iop_clipping_params_t()
            iop_clipping.crop_auto = 0
            iop_clipping.angle = crop_params['angle']
            iop_clipping.cx = crop_params['cx']
            iop_clipping.cy = crop_params['cy']
            iop_clipping.cw = crop_params['cw']
            iop_clipping.ch = crop_params['ch']

            iop_exposure = dt_iop_exposure_params_t()
            iop_exposure.exposure = ev_delta

            xmp_filepath = image_filepath + '.xmp'
            edit_xmp(xmp_filepath, [iop_clipping, iop_exposure])
        except Exception as exc:
            print('Failed to crop %s: %s' % (os.path.basename(image_filepath), exc))

    print('Launching darktable. Reimport all changed .xmp files when prompted.')
    run_darktable([args.directory])


if __name__ == '__main__':
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    subparsers.required = True

    parser_orient = subparsers.add_parser('orient')
    parser_orient.add_argument('directory')
    parser_orient.set_defaults(func=run_orient)

    parser_crop = subparsers.add_parser('crop')
    parser_crop.add_argument('directory')
    parser_crop.set_defaults(func=run_crop)

    args = parser.parse_args()
    args.func(args)
