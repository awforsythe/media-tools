import os
import re


def get_file_range_and_count(dirpath, prefix=None, ext=None):
    lo, hi = None, None
    count = 0

    if os.path.isdir(dirpath):
        regex = re.compile(r'\d+')
        for filename in os.listdir(dirpath):
            basename, file_ext = os.path.splitext(filename)
            if prefix and not basename.lower().startswith(prefix.lower()):
                continue
            if ext and (file_ext.lower() != ext.lower()):
                continue

            match = None
            for match in regex.finditer(basename):
                pass
            if match:
                count += 1
                num = int(match.group(0))
                if lo is None or num < lo:
                    lo = num
                if hi is None or num > hi:
                    hi = num

    return (lo, hi), count
