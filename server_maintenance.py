#!/usr/bin/python3.6
"""
 server maintenance script

"""

import os
import sys
import logging
import argparse
import subprocess
import time

import modules.loadconfig as cfg
import modules.plextools as plex
import modules.processlock as processlock
from modules.galaxymediamod import pushover, diskspace

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"
__progname__ = "server_maintenance"
__description__ = "Server maintenance script"
__detaildesc__ = "Performs OS updates, rootchecks, virus scan, and reboots if necessary"

if cfg.hostname != 'mercury':
    check_drives = {
        "root": "/",
        "incoming": "/mnt/incoming",
        "storage": "/mnt/storage"
        }
else:
    check_drives = {
        "root": "/"
        }

log = logging.getLogger()
parser = argparse.ArgumentParser(prog=__progname__, description=__description__, epilog=__detaildesc__, formatter_class=argparse.RawTextHelpFormatter)
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

def percentof(percent, whole):
  return (percent * whole) / 100.0

def percent(part, whole):
  return 100 * float(part)/float(whole)

def main():
    processlock.lock()
    log.info('Starting disk space checks')
    for drive in check_drives:
        diskres = diskspace(check_drives[drive])
        if percentof(5,int(diskres['MBtotal'])) > int(diskres['MBfree']):
            log.warning('Low disk space on {} {}% Free {} GB of {} GB'.format(drive,lowpercent,int(diskres['GBfree']),int(diskres['GBtotal'])))
            lowpercent = int(percent(int(diskres['MBfree']),int(diskres['MBtotal'])))
            pushover(config.get('pushover', 'security_key'),'Low disk space on {}'.format(myhostname),'{} partition is at {}%\n{} GB Free of {} GB Total'.format(drive,lowpercent,int(diskres['GBfree']),int(diskres['GBtotal'])))
    log.info('Staring OS unattended upgrade process')
    upd = subprocess.Popen(["/usr/bin/python3.5", "/usr/bin/unattended-upgrade"], stdout=subprocess.PIPE)
    returncode = upd.wait()
    if returncode == 0:
        log.info('Unattended-upgrade process completed successfully')
    else:
        log.warning('Unattended-upgrade process returned error code {}'.format(returncode))
    log.info('Starting Sophos antivirus scan')
    sof = subprocess.Popen(["/usr/local/bin/savscan","-s","-narchive","-suspicious","--stay-on-machine","--skip-special","/"], stdout=subprocess.PIPE)
    returncode = sof.wait()
    if returncode == 0:
        log.info('Sophos scan completed and all files are clean')
    elif returncode == 1:
        log.warning('Sophos scan completed and skipped files')
    elif returncode == 2:
        log.error('Sophos scan failed with an error')
    elif returncode == 3:
        log.warning('Sophos scan found a security threat!')
    else:
        log.critical('Sophos scan returned an unknown exit code')
    log.debug('checking to see if a reboot is pending')
    if os.path.isfile('/run/reboot-required'):
        log.info('A pending reboot has been detected')
        if cfg.hostname == cfg.config.get('servers', 'plex_name'):
            x = 0
            while x < 12:
                if plex.isidle_plex():
                    log.info('Rebooting machine')
                    subprocess.Popen(['/sbin/reboot'])
                    exit(0)
                time.sleep(300)
                x += 1
            log.warning('Plex hasnt been idle for over an hour. exiting.')
            exit(2)
        else:
            log.info('Rebooting machine')
            subprocess.Popen(['/sbin/reboot'])
            exit(0)
    else:
        log.debug('no pending reboot is required')


if __name__ == '__main__':
    main()
