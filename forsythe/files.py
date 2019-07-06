import os
import re
import itertools
from collections import defaultdict


def splitext_l(s):
    pos = s.find('.')
    if pos < 0:
        return s, ''
    return s[:pos], s[pos:]


def collect_dirs_and_files(rootdir):
    dirpaths = []
    filepaths = []
    for name in os.listdir(rootdir):
        abspath = os.path.join(rootdir, name)
        if os.path.isdir(abspath):
            dirpaths.append(abspath)
        else:
            filepaths.append(abspath)
    return dirpaths, filepaths


def sort_files_by_ext(filepaths):
    filepaths_by_ext = defaultdict(set)
    for filepath in filepaths:
        ext = splitext_l(filepath)[1].lower()
        filepaths_by_ext[ext].add(filepath)
    return filepaths_by_ext


class FileSequence(object):

    REGEX = re.compile(r'\d+')

    def __init__(self, pattern, numbers):
        self.pattern = pattern
        self.numbers = numbers

    @property
    def ranges(self):
        result = []
        cur_lo = None
        cur_hi = None

        for x in sorted(self.numbers):
            if cur_lo is None:
                cur_lo = x

            if cur_hi is None:
                cur_hi = x
            else:
                if x == cur_hi + 1:
                    cur_hi = x
                else:
                    result.append((cur_lo, cur_hi))
                    cur_lo = x
                    cur_hi = x

        if cur_lo is not None and cur_hi is not None:
            result.append((cur_lo, cur_hi))
        return result

    @classmethod
    def load(cls, filepaths):
        last_dirpath = None
        last_filename_prefix = None
        last_ext = None
        widths = set()
        numbers = set()
        for filepath in filepaths:
            dirpath, filename = os.path.split(filepath)
            if last_dirpath is not None and dirpath != last_dirpath:
                raise ValueError('filepaths must all be in same directory: %s != %s' % (dirpath, last_dirpath))
            last_dirpath = dirpath

            basename, ext = splitext_l(filename)
            if last_ext is not None and ext != last_ext:
                raise ValueError('filepaths must all have the same extension: %s != %s' % (ext, last_ext))
            last_ext = ext

            match = None
            for match in cls.REGEX.finditer(basename):
                pass

            if match:
                filename_prefix = basename[:match.start()]
                if last_filename_prefix is not None and filename_prefix != last_filename_prefix:
                    raise ValueError('filenames must adhere to the same naming format: %s != %s' % (filename_prefix, last_filename_prefix))
                last_filename_prefix = filename_prefix

                number_str = match.group(0)
                width = len(number_str)
                number = int(number_str)

                widths.add(width)
                if width > len(str(number)) and len(widths) > 1:
                    raise ValueError('Mismatched padding widths: %d != %s, widths: %r' % (number, number_str, widths))
                if number in numbers:
                    raise ValueError('Duplicate file number %d in %s' % (number, filepath))
                numbers.add(number)

        if last_dirpath is not None and last_filename_prefix is not None and last_ext is not None and widths and numbers:
            fmt = ('%0' + str(list(widths)[0]) + 'd') if len(widths) == 1 else '%d'
            pattern = os.path.join(last_dirpath, last_filename_prefix + fmt + last_ext)
            return cls(pattern, numbers)
