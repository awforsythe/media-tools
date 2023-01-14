import os

__naps2_install_path_override__ = None


def set_naps2_install_path(dirpath):
    global __naps2_install_path_override__
    __naps2_install_path_override__ = dirpath


def get_naps2_install_path():
    if __naps2_install_path_override__:
        return __naps2_install_path_override__
    program_files_x86 = os.getenv('ProgramFiles(x86)', 'C:\\Program Files (x86)')
    return os.path.join(program_files_x86, 'NAPS2')


def get_naps2_config_path():
    return os.path.join(os.getenv('APPDATA'), 'NAPS2')
