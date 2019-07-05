import os
import json

from .config import get_config_var, set_config_var


def create_collection(rootdir):
    if os.path.isdir(rootdir):
        raise RuntimeError('Collection already exists: %s' % rootdir)
    os.makedirs(rootdir)
    return rootdir


def load_collection(rootdir):
    if not os.path.isdir(rootdir):
        raise RuntimeError('Collection does not exist: %s' % rootdir)
    return rootdir


def produce_collection(rootdir):
    os.makedirs(rootdir, exist_ok=True)
    return rootdir


def load_default_collection():
    rootdir = get_config_var('default_collection')
    if not rootdir:
        raise RuntimeError("No 'default_collection' value is set in config")
    return load_collection(rootdir)


def save_default_collection(rootdir):
    set_config_var('default_collection', rootdir)
