import os
import json


def media_path(*args):
    env_root = os.getenv('FMA_ROOT')
    if not env_root:
        raise RuntimeError('FMA_ROOT not set')
    return os.path.join(env_root, *args)


def load_config():
    try:
        with open(media_path('config.json')) as fp:
            return json.load(fp)
    except RuntimeError:
        return None


def write_config(data):
    with open(media_path('config.json'), 'w') as fp:
        json.dump(data, fp)


def get_selected_collection():
    config = load_config()
    if config:
        return config.get('selected_collection')


def set_selected_collection(type, name, rootdir):
    config = load_config() or {}
    config['selected_collection'] = {
        'type': type,
        'name': name,
        'rootdir': rootdir,
    }
    write_config(config)
