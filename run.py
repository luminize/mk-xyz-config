#!/usr/bin/python

import sys
import os
import subprocess
import argparse
import time
import xyzConfiguration as configuration
from machinekit import launcher
from machinekit import rtapi
from machinekit import config

os.chdir(os.path.dirname(os.path.realpath(__file__)))

parser = argparse.ArgumentParser(description='This is the xyz-configuratin run script '
                                 'it starts the xyz configuration and UI')
parser.add_argument('-nc', '--no_config', help='Disables the config server', action='store_true')
parser.add_argument('-l', '--local', help='Enable local mode only', action='store_true')
parser.add_argument('-s', '--halscope', help='Starts the halscope', action='store_true')
parser.add_argument('-m', '--halmeter', help='Starts the halmeter', action='store_true')
parser.add_argument('-d', '--debug', help='Enable debug mode', action='store_true')
parser.add_argument('-hw', '--hardware', help='Hardware setup', action='store')

args = parser.parse_args()

if args.debug:
    launcher.set_debug_level(5)

if 'MACHINEKIT_INI' not in os.environ:  # export for package installs
    mkconfig = config.Config()
    os.environ['MACHINEKIT_INI'] = mkconfig.MACHINEKIT_INI

def check_mklaucher():
    try:
        subprocess.check_output(['pgrep', 'mklauncher'])
        return True
    except subprocess.CalledProcessError:
        return False

try:
    launcher.check_installation()
    launcher.cleanup_session()
    launcher.start_realtime()
    configuration.check_hardware(args.hardware)
    configuration.setup_hardware(args.hardware)
    configuration.setup_config(args.hardware)
    launcher.register_exit_handler()  # needs to executed after HAL files

    if not check_mklaucher():  # start mklauncher if not running to make things easier
        launcher.start_process('mklauncher .')

    if not args.no_config:
        # the point-of-contact for QtQUickVCP
        launcher.start_process('configserver -n UserInterface .')
    if args.halscope:
        # load scope only now - because all sigs are now defined:
        launcher.start_process('halscope')
    if args.halmeter:
        launcher.start_process('halmeter')

    while True:
        launcher.check_processes()
        time.sleep(1)

except subprocess.CalledProcessError:
    launcher.end_session()
    sys.exit(1)

sys.exit(0)
