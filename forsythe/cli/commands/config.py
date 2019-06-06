import os

from forsythe.cli.commands.common import Command
from forsythe.cli.config import get_config_filepath, load_config


class DumpConfigCommand(Command):

    @classmethod
    def run(self, args):
        filepath = get_config_filepath()
        print('Config file path: %s' % filepath)
        print('File is present.' if os.path.isfile(filepath) else 'File does not exist.')

        print('')
        print('Loaded configuration data:')
        for k, v in sorted(load_config().items()):
            print(' - %s: %r' % (k.rjust(20), v))
