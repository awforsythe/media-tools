import os
import yaml

__config_cache__ = None


def get_config_filepath():
    user_fma_dirpath = os.path.join(os.path.expanduser('~'), '.fma')
    os.makedirs(user_fma_dirpath, exist_ok=True)
    return os.path.join(user_fma_dirpath, 'config.yaml')


def load_config():
    global __config_cache__
    if __config_cache__ is None:
        filepath = get_config_filepath()
        if os.path.isfile(filepath):
            with open(filepath) as fp:
                __config_cache__ = yaml.safe_load(fp) or {}
        else:
            __config_cache__ = {}
    return __config_cache__


def write_config(data):
    global __config_cache__
    filepath = get_config_filepath()
    with open(filepath, 'w') as fp:
        yaml.dump(data, fp)
    __config_cache__ = data


def get_config_var(name, default=None):
    return load_config().get(name, default)


def set_config_var(name, value):
    config = load_config()
    config[name] = value
    write_config(config)
