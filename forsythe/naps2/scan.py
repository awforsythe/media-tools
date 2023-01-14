import os
import subprocess
from forsythe.naps2.paths import get_naps2_install_path


def naps2_scan(profile_name, output_filepath):
    exe_path = os.path.join(get_naps2_install_path(), 'NAPS2.Console.exe')
    args = [exe_path, '-v', '-p', profile_name, '-o', output_filepath]
    subprocess.check_call(args)
