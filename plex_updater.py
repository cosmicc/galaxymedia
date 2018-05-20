#!/usr/bin/python3.6
"""
 plex server software update script

"""

import logging
import argparse
import subprocess

import modules.loadconfig as cfg
import modules.processlock as processlock

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"
__progname__ = "plexupdate"

log = logging.getLogger()
parser = argparse.ArgumentParser(prog=__progname__)
parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
parser.add_argument('-q', '--quiet', action='store_true', help='supress logging output to console. default: error logging')
parser.add_argument('-v', '--verbose', action='store_true', help='verbose output (warning)')
parser.add_argument('-vv', '--info', action='store_true', help='more verbose output (info)')
parser.add_argument('-vvv', '--debug', action='store_true', help='full verbose output (debug)')
parser.add_argument('-l', '--logfile', help='log output to a specified file. default: no log to file')
args = parser.parse_args()
if args.debug == True:
    log.setLevel(logging.DEBUG)
elif args.info == True:
    log.setLevel(logging.INFO)
elif args.verbose == True:
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

def main():
    processlock.lock()
    plexupd = subprocess.Popen(['/opt/plexupdate/plexupdate.sh', '-a', '-d', '-u', '--notify-success', '--config', '/etc/plexupdate.conf'], stdout=subprocess.PIPE)
    result = plexupd.wait()
    if result == 0:
        log.debug('Plex update completed successfully with no updates')
    elif result == 1:
        log.error('Plex update failed with a general error')
    elif result == 4:
        log.error('Plex update failed while downloading the update file')
    elif result == 6:
        log.warning('Plex update was deferred due to server busy')
    elif result == 10:
        log.warning('Plex update has updated the plex server to version {}'.format('version'))
    elif result == 255:
        log.error('Plex update has failed with a configuration error')
    else:
        log.error('Plex update returned an unknown exit code')


if __name__ == '__main__':
    main()
