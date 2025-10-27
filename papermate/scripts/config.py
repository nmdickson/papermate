#!/usr/bin/env python3
'''read and write to the config file easily'''

from papermate.utils import CONFIG, SETTINGS_DEFAULTS

import os
import sys
import shutil
import argparse
import tempfile
import subprocess

try:
    import tomllib as toml
except ImportError:
    import tomli as toml


def read():
    '''Print out the settings in current CONFIG.'''
    sys.stdout.write(f"{CONFIG}\n")


def read_defaults():
    '''Print out the settings in default CONFIG.'''
    out = "\n".join(f"{k} = {v}" for k, v in SETTINGS_DEFAULTS.items()) + "\n"
    sys.stdout.write(out)


def where():
    sys.stdout.write(f"{CONFIG.config_path}\n")


def write():
    '''Open the Config file to edit it, with safety checks.'''

    EDITOR = os.environ.get('EDITOR', 'vim')

    # open the editor and let them write on the file
    with tempfile.NamedTemporaryFile('r+b', suffix=".tmp") as tf:

        shutil.copy(CONFIG.config_path, tf.name)

        while True:

            # write
            # parser.write(tf)  # write the configParser to the temp file
            # tf.flush()
            subprocess.call([EDITOR, tf.name])

            # read
            tf.seek(0)
            # parser.read_file(tf)

            try:
                # TODO should it be this, or try full _Config init?
                toml.load(tf)

                shutil.copy(tf.name, CONFIG.config_path)

                break

            except toml.TOMLDecodeError as err:
                # raise toml.TOMLDecodeError("Invalid config file") from err

                input(f"Invalid config file entered: {err}. [Enter] to retry.")

                continue


def main():

    # ----------------------------------------------------------------------
    # Command line argument parsing
    # ----------------------------------------------------------------------

    parser = argparse.ArgumentParser(
        description='Work with the papermate configuration file.',
        formatter_class=argparse.RawTextHelpFormatter
    )

    help_text = ('"edit" to edit the current config file\n'
                 '"read" to display current config settings (default)\n'
                 '"where" to display current config location\n'
                 '"defaults" to display default config settings')

    parser.add_argument('command', nargs='?', default='read',
                        choices=['edit', 'read', 'where', 'defaults'],
                        help=help_text)

    args = parser.parse_args()

    if args.command == 'read':
        read()
    elif args.command == 'edit':
        write()
    elif args.command == 'where':
        where()
    elif args.command == 'defaults':
        read_defaults()


if __name__ == '__main__':
    main()
