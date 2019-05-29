import os
import glob
import psutil
import subprocess

from forsythe.darktable.files import delete_xmp_files, wait_for_xmp_writes


def get_darktable_binary():
    # TODO: Handle other platforms, allow override via environment variable, check PATH, cache in module-level global
    filepath = 'C:\\Program Files\\darktable\\bin\\darktable.exe'
    if not os.path.isfile(filepath):
        raise RuntimeError('darktable binary not found!')
    return filepath


def get_darktable_processes():
    procs = []
    for proc in psutil.process_iter():
        name = proc.name()
        if os.path.splitext(name)[0].lower() == 'darktable':
            procs.append(proc)
    return procs


def require_darktable_not_running(allow_kill=False):
    for proc in get_darktable_processes():
        if allow_kill:
            proc.kill()
            proc.wait()
        else:
            raise RuntimeError('Unable to continue while darktable is running (pid: %d)' % proc.pid)


def run_darktable(args):
    subprocess.Popen([get_darktable_binary()] + args)


def regenerate_xmps(images_dir):
    if not os.path.isdir(images_dir):
        raise RuntimeError('Invalid photo directory: %s' % images_dir)

    require_darktable_not_running(allow_kill=True)
    delete_xmp_files(images_dir)
    with wait_for_xmp_writes(images_dir):
        run_darktable([images_dir])
    require_darktable_not_running(allow_kill=True)
