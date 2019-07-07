import os
import re
from pynput import keyboard

from forsythe.cli.commands.common import CollectionCommand

from forsythe.files import collect_dirs_and_files, sort_files_by_ext, FileSequence

from forsythe.images.cache import generate_cache, image_iterator
from forsythe.images.params import write_param, read_param

from forsythe.eos.device import wait_for_device
from forsythe.eos.window import activate_liveview, close_eos_windows, capture_liveview_photo
from forsythe.eos.config import update_eos_config, get_image_filepath

from forsythe.interactive import interactive_process


__shoot_keys__ = {
    keyboard.Key.backspace: 'delete',
    keyboard.Key.left: 'capture_left',
    keyboard.Key.right: 'capture_right',
    keyboard.Key.down: 'capture_bottom',
    keyboard.Key.up: 'capture_top',
}


class ShootCommand(CollectionCommand):

    @classmethod
    def init_parser(cls, parser):
        super().init_parser(parser)
        parser.add_argument('subdir', nargs='?', default='.')
        parser.add_argument('--force', '-f', action='store_true')

    @classmethod
    def run(cls, args):
        print('Collection: %s' % os.path.basename(args.collection))
        print('    Subdir: %s' % (args.subdir or '<ROOT>'))
        print('')

        output_dir = os.path.normpath(os.path.join(args.collection, args.subdir))
        start_num = 1
        num_prefix = args.subdir[0] if args.subdir and args.subdir != 'images' else ''
        pattern = os.path.join(output_dir, '%s_%s' % (os.path.basename(args.collection), num_prefix)) + '%04d.CR2'

        print("Writing to: %s" % output_dir)
        _, filepaths = collect_dirs_and_files(output_dir)
        existing_cr2_files = sort_files_by_ext(filepaths).get('.cr2')
        if existing_cr2_files:
            print('%d existing images:' % len(existing_cr2_files))
            seq = FileSequence.load(existing_cr2_files)
            for range in seq.ranges:
                print(' - ranging from %d to %d' % range)
                start_num = range[1] + 1
                pattern = seq.pattern
        else:
            print('No existing images.')
        print('')
        prefix = os.path.basename(pattern[:pattern.rfind(r'%')])

        print('Capture will start from:')
        print(' - %s' % (pattern % start_num))
        print('')

        print('Pre-capture checklist:')
        print('')
        print('  1. Arrange lights.')
        print('  2. Disable OIS in lens.')
        print('  3. Ensure that lens zoom is not extreme.')
        print('  4. Ensure that camera height exceeds minimum macro distance.')
        print('  5. Set shooting mode to full manual.')
        print('  6. Find appropriate exposure around f/5.6.')
        print('  7. Take full-frame photo of 18% gray card.')
        print('  8. Set that photo as source for custom white balance.')
        print('  9. Set white balance mode to Custom.')
        print(' 10. Ensure that color-keyable background fills frame.')
        print('')
        if not args.force:
            print('Proceed?')
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

        print("escape: exit | up/down/left/right: capture | backspace: delete last")
        print("Waiting for input...")
        image_num = start_num
        delete_prompted = False
        for command in interactive_process(__shoot_keys__):
            if delete_prompted:
                if command == 'delete':
                    raw_filepath = pattern % (image_num - 1)
                    os.remove(raw_filepath)
                    print('Deleted %s' % raw_filepath)
                    xmp_filepath = raw_filepath + '.xmp'
                    if os.path.isfile(xmp_filepath):
                        os.remove(xmp_filepath)
                        print('Deleted %s' % xmp_filepath)
                    image_num -= 1
                    close_eos_windows()
                    update_eos_config(output_dir, prefix, image_num)
                    activate_liveview()
                else:
                    print('Cancelled delete.')
                delete_prompted = False
            elif command == 'delete':
                raw_filepath = pattern % (image_num - 1)
                if os.path.isfile(raw_filepath):
                    print('Press backspace again to delete %s...' % os.path.basename(raw_filepath))
                    delete_prompted = True
                else:
                    print('No such file: %s' % raw_filepath)
            elif command.startswith('capture'):
                raw_filepath = pattern % image_num
                top_edge = command.replace('capture_', '')
                write_param(raw_filepath, 'top_edge', top_edge)
                print('%s --> %s' % (raw_filepath, top_edge))
                capture_liveview_photo()
                image_num += 1

        print('Finished.')
        close_eos_windows()
        print('Turn camera power off to conserve battery.')
