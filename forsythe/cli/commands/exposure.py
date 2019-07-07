import os
import re

from forsythe.cli.commands.common import CollectionCommand
from forsythe.files import collect_dirs_and_files, sort_files_by_ext, FileSequence
from forsythe.images.params import write_param, read_param


class ShiftExposureCommand(CollectionCommand):

    @classmethod
    def init_parser(cls, parser):
        super().init_parser(parser)
        parser.add_argument('subdir', nargs='?', default='.')
        parser.add_argument('ev_delta', type=float)

    @classmethod
    def run(cls, args):
        print('Collection: %s' % os.path.basename(args.collection))
        print('    Subdir: %s' % (args.subdir or '<ROOT>'))
        print('')

        images_dir = os.path.normpath(os.path.join(args.collection, args.subdir))
        _, filepaths = collect_dirs_and_files(images_dir)
        filepaths_by_ext = sort_files_by_ext(filepaths)
        cr2_files = filepaths_by_ext.get('.cr2', [])
        if cr2_files:
            seq = FileSequence.load(cr2_files)
            if seq:
                range_str = ', '.join(['(%d-%d)' % (lo, hi) for lo, hi in seq.ranges])
                print('%d image files found: %s' % (len(cr2_files), range_str))
            else:
                print('%d image files found.' % len(cr2_files))
        else:
            raise RuntimeError('No .cr2 image files found')

        print('Setting exposure delta to %+0.2f EV...' % args.ev_delta)
        print('')
        changed_count = 0
        unchanged_count = 0
        for image_filepath in sorted(cr2_files):
            old_ev_delta = read_param(image_filepath, 'ev_delta', 0.0)
            if old_ev_delta == args.ev_delta:
                unchanged_count += 1
            else:
                print('%s: %+0.2f EV --> %+0.2f EV' % (os.path.basename(image_filepath), old_ev_delta, args.ev_delta))
                write_param(image_filepath, 'ev_delta', args.ev_delta)
                changed_count += 1
        print('')
        print('Updated params for %d images; left %d images unchanged.' % (changed_count, unchanged_count))
        if changed_count:
            print('Run fma dt-apply to apply changes to .xmp files.')
