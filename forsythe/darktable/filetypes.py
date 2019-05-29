import os

__image_exts__ = ['.raw', '.cr2', '.png', '.jpg', '.jpeg']


def list_image_filenames(images_dir):
    filenames = []
    for filename in os.listdir(images_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext in __image_exts__:
            filenames.append(ext)
    return filenames
