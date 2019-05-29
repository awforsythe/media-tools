import os
import json

__params_dirname__ = '.params'
__params_ext__ = '.json'


def get_params_filepath(image_filepath, for_write=False):
    dirname, filename = os.path.split(image_filepath)
    basename = os.path.splitext(filename)[0]
    dirpath = os.path.join(dirname, __params_dirname__)
    if for_write:
        os.makedirs(dirpath, exist_ok=True)
    return os.path.join(dirpath, basename + __params_ext__)


def write_params(image_filepath, params):
    filepath = get_params_filepath(image_filepath, for_write=True)
    with open(filepath, 'w') as fp:
        json.dump(params, fp)


def read_params(image_filepath):
    filepath = get_params_filepath(image_filepath)
    if os.path.isfile(filepath):
        with open(filepath) as fp:
            return json.load(fp)
    return {}


def write_param(image_filepath, key, value):
    params = read_params(image_filepath)
    params[key] = value
    write_params(image_filepath, params)


def read_param(image_filepath, key, default=None):
    return read_params(image_filepath).get(key, default)
