import os

from forsythe.cli.commands.common import Command, CollectionCommand
from forsythe.collections import create_collection, load_collection, load_default_collection, save_default_collection
from forsythe.files import collect_dirs_and_files, sort_files_by_ext, FileSequence


class MakeCommand(Command):

    @classmethod
    def init_parser(cls, parser):
        parser.add_argument('relpath', nargs='?', default='.')
        parser.add_argument('--select', '-s', action='store_true')

    @classmethod
    def run(cls, args):
        abspath = create_collection(os.path.abspath(args.relpath))
        print('Created collection: %s' % abspath)
        if args.select:
            save_default_collection(abspath)
            print('Selected collection.')


class SelectCommand(Command):

    @classmethod
    def init_parser(cls, parser):
        parser.add_argument('relpath', nargs='?', default='.')

    @classmethod
    def run(cls, args):
        abspath = load_collection(os.path.abspath(args.relpath))
        save_default_collection(abspath)
        print('Selected collection: %s' % abspath)


class ReportCommand(CollectionCommand):

    @classmethod
    def run(cls, args):

        def aux(rootdir, level=0):
            pad = ' ' * level
            dirpaths, filepaths = collect_dirs_and_files(rootdir)
            filepaths_by_ext = sort_files_by_ext(filepaths)
            if filepaths_by_ext:
                for ext, filepaths in sorted(filepaths_by_ext.items()):
                    seq = FileSequence.load(filepaths)
                    if seq:
                        range_str = ', '.join(['(%d-%d)' % (lo, hi) for lo, hi in seq.ranges])
                        print('%s %s | %4d | %s' % (pad, ext.ljust(8), len(filepaths), range_str))
                    else:
                        print('%s %s | %4d ' % (pad, ext.ljust(8), len(filepaths)))
            elif not dirpaths:
                print('%s (empty)' % pad)

            for dirpath in dirpaths:
                print('%s %s:' % (pad, os.path.basename(dirpath)))
                aux(dirpath, level + 1)

        print(args.collection)
        aux(args.collection)
