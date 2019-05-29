import os

__image_exts__ = ['.raw', '.cr2', '.png', '.jpg', '.jpeg']
__raw_exts__ = ['.raw', '.cr2']


def list_image_filenames(images_dir):
    filenames = []
    for filename in os.listdir(images_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext in __image_exts__:
            filenames.append(filename)
    return filenames


def is_raw(filename):
    return os.path.splitext(filename)[1].lower() in __raw_exts__


def list_raw_image_filenames(images_dir):
    return [filename for filename in list_image_filenames(images_dir) if is_raw(filename)]
