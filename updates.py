#!/usr/bin/python3

import logging
import subprocess

log = logging.getLogger()
console_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
log_console = logging.StreamHandler()
log.addHandler(log_console)
log_console.setFormatter(console_format)
log.setLevel(logging.DEBUG)

log.info('Staring OS unattended upgrade process')
upd = subprocess.Popen(["/usr/bin/unattended-upgrade"], stdout=subprocess.PIPE)
returncode = upd.wait()
if returncode == 0:
    log.info('Unattended-upgrade process completed successfully')
else:
    log.warning('Unattended-upgrade process returned error code {}'.format(returncode))

log.info('Starting Sophos antivirus scan')
sof = subprocess.Popen(["/usr/local/bin/savscan","-s","-narchive","-suspicious","--stay-on-machine","--skip-special","/"], stdout=subprocess.PIPE)
returncode = upd.wait()
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



