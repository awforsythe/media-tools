import os
import argparse
import multiprocessing
import cv2
from queue import Queue
from pynput import keyboard

from forsythe.collections.common import media_path, get_selected_collection, set_selected_collection
from forsythe.collections.filerange import get_file_range_and_count

from forsythe.images.cache import generate_cache, image_iterator
from forsythe.images.params import write_param, read_param

from forsythe.eos.device import wait_for_device
from forsythe.eos.window import activate_liveview, close_eos_windows, capture_liveview_photo
from forsythe.eos.config import update_eos_config, get_image_filepath

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


def run_list(args):
    dirpath = media_path(args.type)
    collection_names = []
    if os.path.isdir(dirpath):
        for dirname in os.listdir(dirpath):
            if os.path.isdir(os.path.join(dirpath, dirname)) and not dirname.startswith('.') and not dirname.startswith('_'):
                collection_names.append(dirname)

    selected_collection = get_selected_collection() or {}
    selected_type = selected_collection.get('type')
    selected_name = selected_collection.get('name')

    if collection_names:
        print("Collections of type '%s':" % args.type)
        for name in sorted(collection_names):
            is_selected = selected_type == args.type and selected_name == name
            prefix = '=> ' if is_selected else ' - '
            suffix = ' <= *SELECTED*' if is_selected else ''
            print(prefix + name + suffix)
    else:
        print("No collections of type '%s'." % args.type)


def run_select(args):
    directory = args.directory.replace('/', os.sep).replace('\\', os.sep)
    dirnames = directory.split(os.sep)
    if os.path.isabs(directory) or directory.startswith('.'):
        collection_type = args.type or dirnames[-2]
        collection_name = dirnames[-1]
        rootdir = os.path.abspath(directory)
    else:
        assert len(dirnames) <= 2
        collection_type = args.type or (dirnames[0] if len(dirnames) > 1 else 'photos')
        collection_name = dirnames[-1]
        rootdir = media_path(collection_type, collection_name)

    if not os.path.isdir(rootdir):
        os.makedirs(rootdir)
        print("Created: %s" % rootdir)

    set_selected_collection(collection_type, collection_name, rootdir)
    print("Selected collection '%s' of type '%s'." % (collection_name, collection_type))


def run_shoot(args):
    selected_collection = get_selected_collection()
    if not selected_collection:
        raise RuntimeError('No collection selected!')

    collection_type = selected_collection.get('type')
    collection_name = selected_collection.get('name')
    print("Shooting in '%s' collection '%s'." % (collection_type, collection_name))
    print("Subdirectory: %s" % args.subdir)

    output_dir = os.path.join(selected_collection.get('rootdir'), args.subdir) if args.subdir else selected_collection.get('rootdir')
    print("Writing to: %s" % output_dir)

    prefix = '%s_%s' % (collection_name, args.subdir[0] if args.subdir and args.subdir != 'images' else '')
    (lo, hi), count = get_file_range_and_count(output_dir, prefix=prefix, ext='.cr2')

    print("")
    if not count:
        print("Directory is empty (no existing images).")
        start_num = 1
    else:
        print("Directory contains %d existing images (numbered from %d to %d)." % (count, lo, hi))
        start_num = hi + 1
    print("Capture will start from: %s%04d.CR2" % (prefix, start_num))

    print("")
    print("Pre-capture checklist:")
    print("")
    print("  1. Arrange lights.")
    print("  2. Disable OIS in lens.")
    print("  3. Ensure that lens zoom is not extreme.")
    print("  4. Ensure that camera height exceeds minimum macro distance.")
    print("  5. Set shooting mode to full manual.")
    print("  6. Find appropriate exposure around f/5.6.")
    print("  7. Take full-frame photo of 18% gray card.")
    print("  8. Set that photo as source for custom white balance.")
    print("  9. Set white balance mode to Custom.")
    print(" 10. Ensure that color-keyable background fills frame.")
    print("")
    if not args.force:
        print("Proceed?")
        choice = input('> ')
        if choice.lower() not in ('y', 'yes'):
            print("Abort.")
            return

    wait_for_device()

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
        print("Created: %s" % output_dir)

    close_eos_windows()
    update_eos_config(output_dir, prefix, start_num)
    activate_liveview()

    delete_prompted = [False]
    queue = Queue()

    def on_key(key):
        if key == keyboard.Key.esc:
            queue.put('exit')
            return False
        if key == keyboard.Key.backspace:
            queue.put('delete' if delete_prompted[0] else 'prompt_delete')
            return False
        if key == keyboard.Key.left:
            queue.put('capture_left')
            return False
        if key == keyboard.Key.right:
            queue.put('capture_right')
            return False
        if key == keyboard.Key.down:
            queue.put('capture_bottom')
            return False
        if key == keyboard.Key.up:
            queue.put('capture_top')
            return False

    print("escape: exit | up/down/left/right: capture | backspace: delete last")
    print("Waiting for input...")
    image_num = start_num
    while True:
        with keyboard.Listener(on_release=on_key) as listener:
            listener.join()
        event = queue.get()

        if delete_prompted[0]:
            if event == 'delete':
                raw_filepath = get_image_filepath(image_num - 1)
                os.remove(raw_filepath)
                print("Deleted %s" % raw_filepath)
                xmp_filepath = raw_filepath + '.xmp'
                if os.path.isfile(xmp_filepath):
                    os.remove(xmp_filepath)
                    print("Deleted %s" % xmp_filepath)
                image_num -= 1
                close_eos_windows()
                update_eos_config(output_dir, prefix, image_num)
            else:
                print("Cancelled delete.")
            delete_prompted[0] = False
        elif event == 'exit':
            break
        elif event == 'prompt_delete':
            raw_filepath = get_image_filepath(image_num - 1)
            if os.path.isfile(raw_filepath):
                print("Press Backspace again to delete %s..." % os.path.basename(raw_filepath))
                delete_prompted[0] = True
        elif event.startswith('capture'):
            raw_filepath = get_image_filepath(image_num)
            top_edge = event.replace('capture_', '')
            write_param(raw_filepath, 'top_edge', top_edge)
            print('%s --> %s' % (raw_filepath, top_edge))
            capture_liveview_photo()
            image_num += 1

    print("Finished.")
    close_eos_windows()
    print("Turn camera power off to conserve battery.")


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
        image_params = read_params(image_filepath)
        ev_delta = 0.4

        try:
            crop_params = compute_crop_params(cached_filepath, image_params)
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

    parser_list = subparsers.add_parser('list')
    parser_list.add_argument('type', nargs='?', default='photos')
    parser_list.set_defaults(func=run_list)

    parser_select = subparsers.add_parser('select')
    parser_select.add_argument('directory')
    parser_select.add_argument('--type', '-t')
    parser_select.set_defaults(func=run_select)

    parser_shoot = subparsers.add_parser('shoot')
    parser_shoot.add_argument('subdir', nargs='?')
    parser_shoot.add_argument('--force', '-f', action='store_true')
    parser_shoot.set_defaults(func=run_shoot)

    parser_orient = subparsers.add_parser('orient')
    parser_orient.add_argument('directory')
    parser_orient.set_defaults(func=run_orient)

    parser_crop = subparsers.add_parser('crop')
    parser_crop.add_argument('directory')
    parser_crop.set_defaults(func=run_crop)

    args = parser.parse_args()
    args.func(args)
