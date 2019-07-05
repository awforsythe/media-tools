import os
import json


__fma_json_path__ = os.path.join(os.path.expanduser('~'), '.fma.json')


def get_config_filepath():
    return __fma_json_path__


def load_config():
    try:
        with open(__fma_json_path__) as fp:
            return json.load(fp) or {}
    except OSError:
        return {}


def write_config(data):
    with open(__fma_json_path__, 'w') as fp:
        json.dump(data, fp, indent=4, sort_keys=True)


def get_config_var(name, default=None):
    return load_config().get(name, default)


def set_config_var(name, value):
    data = load_config()
    data[name] = value
    write_config(data)
