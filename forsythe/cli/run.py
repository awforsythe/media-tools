import os
import sys
import importlib
import argparse

__commands__ = [
    {
        'name': 'dump-config', 'module': 'config',
        'help': 'Dump contents of FMA config file to stdout'
    },
    {
        'name': 'edit-config', 'module': 'config',
        'help': 'Open FMA config file for manual editing'
    },
    {
        'name': 'make', 'module': 'collections',
        'help': 'Create a new collection, and optionally selects it'
    },
    {
        'name': 'select', 'module': 'collections',
        'help': 'Sets the currently selected collection'
    },
    {
        'name': 'report', 'module': 'collections',
        'help': 'Reports on the contents of the selected collection',
    }
]


def print_commands():
    print('Usage: fma <command-name> <command-args>')
    print('For individual command options: fma <command-name> -h')
    print('')
    print('Valid commands:')
    for command in __commands__:
        print(" %s | %s" % (command['name'].ljust(16), command.get('help', '')))


def get_class_name(command_def):
    class_name = command_def.get('class')
    if class_name:
        return class_name
    return ''.join([s.title() for s in command_def['name'].split('-')]) + 'Command'


def get_module_path(command_def):
    module_path = command_def.get('module')
    if not module_path:
        module_path = command_def['name'].replace('-', '_')
    if '.' not in module_path:
        return 'forsythe.cli.commands.%s' % module_path
    return module_path


def run_cli():
    command_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if not command_arg or command_arg in ('-h', '--help', '/?'):
        print_commands()
        return 1

    command_def = next((c for c in __commands__ if c['name'] == command_arg), None)
    if not command_def:
        print("ERROR: Command type '%s' is not recognized" % command_arg)
        print_commands()
        return 1

    package_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sys.path.append(package_root)

    class_name = get_class_name(command_def)
    module_path = get_module_path(command_def)
    module = importlib.import_module(module_path)

    command_class_name = get_class_name(command_def)
    command_class = getattr(module, command_class_name)

    parser = argparse.ArgumentParser()
    command_class.init_parser(parser)
    args = parser.parse_args(sys.argv[2:])
    command_class.run(args)
    return 0


if __name__ == '__main__':
    sys.exit(run_cli())
