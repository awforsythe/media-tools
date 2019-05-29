import os
import multiprocessing

import rawpy
import imageio

from forsythe.images.files import list_image_filenames, is_raw, list_raw_image_filenames

__cache_dirname__ = '.imagecache'


def get_cached_image_filepath(raw_filepath):
    dirpath, filename = os.path.split(raw_filepath)
    basename = os.path.splitext(filename)[0]
    return os.path.join(dirpath, __cache_dirname__, basename + '.jpg')


def regenerate_cached_image(raw_filepath):
    with rawpy.imread(raw_filepath) as raw:
        rgb = raw.postprocess()
        imageio.imsave(get_cached_image_filepath(raw_filepath), rgb)


def generate_cache(images_dir, force=False, multiprocess=True):
    cache_dir = os.path.join(images_dir, __cache_dirname__)
    os.makedirs(cache_dir, exist_ok=True)

    raw_filepaths_to_regenerate = []
    for raw_filename in list_raw_image_filenames(images_dir):
        raw_filepath = os.path.join(images_dir, raw_filename)
        if force or not os.path.isfile(get_cached_image_filepath(raw_filepath)):
            raw_filepaths_to_regenerate.append(raw_filepath)

    if multiprocess:
        pool = multiprocessing.Pool()
        pool.map(regenerate_cached_image, raw_filepaths_to_regenerate)
    else:
        for raw_filepath in raw_filepaths_to_regenerate:
            regenerate_cached_image(raw_filepath)


def image_iterator(images_dir):
    for filename in list_image_filenames(images_dir):
        filepath = os.path.join(images_dir, filename)
        if is_raw(filepath):
            cached_filepath = get_cached_image_filepath(filepath)
            if not os.path.isfile(cached_filepath):
                regenerate_cached_image(filepath)
            yield filepath, cached_filepath
        else:
            yield filepath, filepath
