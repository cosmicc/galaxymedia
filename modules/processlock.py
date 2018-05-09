#!/usr/bin/python3

import os
import sys
import time
import fcntl
import logging
import atexit

log = logging.getLogger(__name__)


def cleanName(filename):
    filename = os.path.basename(filename)
    filename = filename.rsplit('.', 1)[0]
    return filename


def lock():
    ppid = str(os.getpid())

    def aquireLock():
        if not os.path.isfile(lockfile):
            os.mknod(lockfile, mode=0o600)
        try:
            fcntl.lockf(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            return False
        except:
            log.exception('General error trying to lock process to file {}. exiting.'.format(lockfile))
            exit(1)
        else:
            log.info('Process has been locked to file {} with PID [{}]'.format(lockfile, ppid))
            return True
    if aquireLock():
        # lock_handle = open(lockfile, 'w')
        lock_handle.write(ppid)
        # lock_handle.close()
        atexit.register(unlock)
        return True
    else:
        # do pid checking
        log.warning('Process is locked. Another instance is running. Retrying every 5 seconds until timeout')
        time.sleep(5)
    for numtries in range(12):
        if aquireLock():
            lock_handle.write(ppid)
            atexit.register(unlock)
            return True
        else:
            time.sleep(5)
    log.error('Could not obtain process lock after 60 seconds. Exiting')
    exit(1)


def unlock():
    fcntl.flock(lock_handle, fcntl.LOCK_UN)
    lock_handle.close()
    # if os.path.isfile(lockfile):
    #    os.remove(lockfile)


if os.path.isdir('/run'):
    lpath = '/run'
elif os.path.isdir('/var/tmp'):
    lpath = '/var/tmp'
else:
    log.critical('Cannot find a valid place to put the lockfile. Exiting')
    exit(1)

lockfile = '{}/{}.lock'.format(lpath, cleanName(sys.argv[0]))
lock_handle = open(lockfile, 'w')
