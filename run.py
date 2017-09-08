#!/usr/bin/python

import sys
import os
import subprocess
import argparse
import time
import xyzConfiguration as configuration
from machineclass import MiniMachine
from machinekit import launcher
from machinekit import rtapi
from machinekit import config


def tickle_machine(machine):
    machine.process_queue()


def check_mklaucher():
    try:
        subprocess.check_output(['pgrep', 'mklauncher'])
        return True
    except subprocess.CalledProcessError:
        return False

    
def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    parser = argparse.ArgumentParser(description='This is the xyz-configuratin run script '
                                 'it starts the xyz configuration and UI')
    parser.add_argument('-nc', '--no_config', help='Disables the config server', action='store_true')
    parser.add_argument('-l', '--local', help='Enable local mode only', action='store_true')
    parser.add_argument('-s', '--halscope', help='Starts the halscope', action='store_true')
    parser.add_argument('-m', '--halmeter', help='Starts the halmeter', action='store_true')
    parser.add_argument('-d', '--debug', help='Enable debug mode', action='store_true')
    parser.add_argument('-hw', '--hardware', help='Hardware setup', action='store')
    parser.add_argument('-t', '--test', help='Connect test motor to siggen', action='store_true')
    parser.add_argument('-mh', '--manhole', help='Enable manhole', action='store_true')

    args = parser.parse_args()

    if args.debug:
        launcher.set_debug_level(5)

    if 'MACHINEKIT_INI' not in os.environ:  # export for package installs
        mkconfig = config.Config()
        os.environ['MACHINEKIT_INI'] = mkconfig.MACHINEKIT_INI
            
    try:
        launcher.check_installation()
        launcher.cleanup_session()
        launcher.load_bbio_file('cramps2_cape.bbio')
        launcher.start_realtime()
        
        # setup of configuration
        configuration.check_hardware(args.hardware)
        configuration.setup_hardware(args.hardware)
        configuration.setup_config(args.hardware)
        if args.test:
            # setup motor stepgen with siggen:
            configuration.setup_test_cramps()
        configuration.start_hal()
        # instantiate machine
        m=MiniMachine(name='m')
    
        if args.manhole:
            try:
                import manhole
                manhole.install(locals={
                    'm' : m
                })
            except Exception:
                print "manhole not installed - run 'sudo pip install manhole'"

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
            m.process_queue()
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    launcher.end_session()
    sys.exit(0)


if __name__ == "__main__":
    main()

