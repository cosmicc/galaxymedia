#!/usr/bin/python3
"""
    Watchdog for vpn connection on mercury
"""
import os
import sys
import time
import logging
import argparse

import subprocess

sys.path.insert(0, '/opt/galaxymodules')
import proctools

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"


def main():
    log = logging.getLogger()
    parser = argparse.ArgumentParser(prog='vpncheck')
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output (info)')
    parser.add_argument('-vv', '--debug', action='store_true', help='full verbose output (debug)')
    parser.add_argument('-l', '--logfile', help='file to log output to. default: log to console (no file logging)')
    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)
    elif args.verbose:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.WARNING)

    log_format = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')

    if args.logfile is None:
        log_handler = logging.StreamHandler()
    else:
        log_handler = logging.FileHandler(args.logfile)
    log_handler.setFormatter(log_format)
    log.addHandler(log_handler)

    log.debug('checking internet connectivity')
    cresult = subprocess.call(['/usr/bin/fping', '-q', '1.1.1.1'], shell=False)
    if cresult != 0:
        log.warning('Internet down. Restarting VPN...')
        log.debug('Executing \'service vpn stop\'')
        try:
            os.system('/usr/sbin/service vpn stop')
        except:
            log.exception('Error executing service vpn stop')
        proctools.kill_all('openvpn')
        try:
            os.system('/usr/bin/killall openvpn')
        except:
            log.exception('Error executing killall openvpn')
        log.debug('Executing \'Sleeping 3 seconds\'')
        time.sleep(3)
        log.debug('Executing \'service vpn start \'')
        try:
            os.system('/usr/sbin/service vpn start')
        except:
            log.exception('Error executing service vpn start')
    else:
        log.debug('Internet is up. Nothing to do.')


if __name__ == '__main__':
    main()
