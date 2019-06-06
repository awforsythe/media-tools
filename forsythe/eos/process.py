import os
import subprocess


def get_eos_utility_binary():
    # TODO: Handle other platforms, allow override via environment variable, check PATH, cache in module-level global
    filepath = 'C:\\Program Files (x86)\\Canon\\EOS Utility\\EOS Utility.exe'
    if not os.path.isfile(filepath):
        raise RuntimeError('EOS Utility binary not found!')
    return filepath


def run_eos_utility():
    subprocess.Popen([get_eos_utility_binary()])
