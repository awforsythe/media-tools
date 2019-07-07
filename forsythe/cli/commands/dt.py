import os
import re

from forsythe.cli.commands.common import CollectionCommand
from forsythe.files import collect_dirs_and_files, sort_files_by_ext, FileSequence
from forsythe.images.cache import generate_cache, image_iterator
from forsythe.images.params import read_param
from forsythe.darktable.process import regenerate_xmps, run_darktable
from forsythe.darktable.iop import dt_iop_clipping_params_t, dt_iop_exposure_params_t
from forsythe.darktable.xmp import edit_xmp
from forsythe.cropper import compute_crop_params


class DtClearCommand(CollectionCommand):

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

        images_dir = os.path.normpath(os.path.join(args.collection, args.subdir))
        _, filepaths = collect_dirs_and_files(images_dir)
        xmp_files = sort_files_by_ext(filepaths).get('.cr2.xmp', [])
        if xmp_files:
            seq = FileSequence.load(xmp_files)
            if seq:
                range_str = ', '.join(['(%d-%d)' % (lo, hi) for lo, hi in seq.ranges])
                print('%d sidecar files found: %s' % (len(xmp_files), range_str))
            else:
                print('%d sidecar files found.' % len(xmp_files))

            if not args.force:
                print('')
                print('These existing sidecar files contain edits made in darktable.')
                print('Clearing these files will DELETE these previously-made edits.')
                print('If you\'re sure you want to do that, re-run with -f.')
                return
        else:
            print('No .xmp sidecar files found.')
            return

        print('')
        print('Deleting %d sidecar files...' % len(xmp_files))
        num_deleted = 0
        for filepath in xmp_files:
            print('DELETE %s' % os.path.basename(filepath))
            os.remove(filepath)
            num_deleted += 1

        print('')
        print('Deleted %d files.' % num_deleted)



class DtApplyCommand(CollectionCommand):

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

        xmp_files = filepaths_by_ext.get('.cr2.xmp', [])
        if xmp_files:
            seq = FileSequence.load(xmp_files)
            if seq:
                range_str = ', '.join(['(%d-%d)' % (lo, hi) for lo, hi in seq.ranges])
                print('%d sidecar files found: %s' % (len(xmp_files), range_str))
            else:
                print('%d sidecar files found.' % len(xmp_files))

            if not args.force:
                print('')
                print('These existing sidecar files contain edits made in darktable.')
                print('Applying these edits will DELETE these previously-made edits.')
                print('If you\'re sure you want to do that, re-run with -f.')
                return

        print('')
        print('Generating image cache...')
        generate_cache(images_dir)

        print('Regenerating .xmp sidecar files...')
        regenerate_xmps(images_dir)

        for image_filepath, cached_filepath in image_iterator(images_dir):
            iops = []

            top_edge = read_param(image_filepath, 'top_edge', 'top')
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
                iops.append(iop_clipping)
            except Exception as exc:
                print('WARNING: Failed to crop %s: %s' % (os.path.basename(image_filepath), exc))

            ev_delta = read_param(image_filepath, 'ev_delta')
            if ev_delta:
                iop_exposure = dt_iop_exposure_params_t()
                iop_exposure.exposure = ev_delta
                iops.append(iop_exposure)

            xmp_filepath = image_filepath + '.xmp'
            if iops:
                edit_xmp(xmp_filepath, iops)
                print('%s: %s' % (os.path.basename(xmp_filepath), ', '.join([iop.operation for iop in iops])))
            else:
                print('%s: <skipped>' % (os.path.basename(xmp_filepath)))

        print('Launching darktable. Reimport all changed .xmp files when prompted.')
        run_darktable([images_dir])


class DtOpenCommand(CollectionCommand):

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
        print('')

        print('Launching darktable...')
        run_darktable([images_dir])
