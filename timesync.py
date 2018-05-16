#!/usr/bin/python3.6
"""
 server maintenance script

"""

import logging
import argparse
from time import ctime
import subprocess

from ntplib import NTPClient

from modules.galaxymediamod import require_root
import modules.loadconfig as cfg
import modules.processlock as processlock

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"
__progname__ = "timesync"

log = logging.getLogger()
parser = argparse.ArgumentParser(prog=__progname__)
parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
parser.add_argument('-q', '--quiet', action='store_true', help='supress logging output to console. default: error logging')
parser.add_argument('-v', '--verbose', action='store_true', help='verbose output (warning)')
parser.add_argument('-vv', '--info', action='store_true', help='more verbose output (info)')
parser.add_argument('-vvv', '--debug', action='store_true', help='full verbose output (debug)')
parser.add_argument('-l', '--logfile', help='log output to a specified file. default: no log to file')
args = parser.parse_args()
if args.debug:
    log.setLevel(logging.DEBUG)
elif args.info:
    log.setLevel(logging.INFO)
elif args.verbose:
    log.setLevel(logging.WARNING)
else:
    log.setLevel(logging.ERROR)
console_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
log_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
if args.quiet is False:
    log_console = logging.StreamHandler()
    log.addHandler(log_console)
    log_console.setFormatter(console_format)
if args.logfile is not None:
    log_fileh = logging.FileHandler(args.logfile)
    log.addHandler(log_fileh)
    log_fileh.setFormatter(log_format)


def checktime():
    require_root()
    ntp = NTPClient()
    timeservers = cfg.config.getlist('general', 'time_servers')
    for tserver in timeservers:
        log.debug('Trying time server [{}]'.format(tserver))
        try:
            response = ntp.request(tserver, version=3)
        except:
            log.warning('Time server [{}] is not responding, trying next server'.format(tserver))
        else:
            newtime = ctime(response.tx_time)
            log.info('Time server [{}] returned [{}] with an offset of \
                     {}'.format(tserver,newtime,response.offset))
            log.debug('Updating system time with new queried time')
            cmddate = subprocess.Popen(['date', '-s', newtime], stdout=subprocess.PIPE)
            return cmddate.wait()

def main():
    require_root()
    processlock.lock()
    returncode = checktime()
    if returncode == 0:
        log.info('System time updated successfully')
        exit(0)
    else:
        log.error('System time failed to update')
        exit(1)


if __name__ == '__main__':
    main()
