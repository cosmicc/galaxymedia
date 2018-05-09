"""
 process tools module

 various custom process functions created for my own use

 get_pids(name) - returns list of PIDS by process name
 kill_pids(pids) - returns bool if list of PIDS are dead
 kill_all(name) - returns bool after all pids from process are killed (gracefully)
 pidkill_gracefully(pid) - returns bool after killing pid gracefully
 piddead(pid) - returns bool if pid is piddead
"""

import os
import time
import logging
from subprocess import check_output
from signal import SIGTERM, SIGINT, SIGHUP, SIGKILL, Signals

log = logging.getLogger(__name__)


def ispid_running(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def kill_all(name):
    allpids = get_pids(name)
    if len(allpids) == 0:
        log.debug('kill_all: no processes to kill, no pids found for \'{}\''.format(name))
        return True
    else:
        kill_pids(allpids)


def get_pids(name):
    try:
        pids = list(map(int, check_output(["pidof", name]).split()))
        log.debug('get_pids: pid from process found: \'{}\' is {}'.format(name, pids))
    except Exception as e:
        log.debug('get_pids: pid from process not found: \'{}\''.format(name))
        pids = []
    finally:
        return pids


def kill_pids(pids):
    if not isinstance(pids, list):
        log.error('kill_pids: non list type sent to kill_pids function')
        return False
    else:
        if len(pids) == 0:
            log.warning('kill_pids: empty pid list passed to kill_pids function')
            return True
        else:
            log.debug('kill_pids: trying to kills pids {}'.format(pids))
            for pid in pids:
                try:
                    pidkill_gracefully(pid)
                except:
                    log.exception('kill_pids: exception thrown while killing pid [{}]'.format(pid))
                else:
                    log.debug('kill_pids: pid [{}] has been successfully terminated'.format(pid))
            log.debug('kill_pids: completed killing pids: {}'.format(pids))
            isproc = False
            for pid in pids:
                if not piddead(pid):
                    log.warning('kill_pids: still running after kill attempt pid [{}]'.format(pid))
                    isproc = True
            if isproc:
                log.warning('kill_pids: processes are still running after kill attempts. Returning False.')
            else:
                log.debug('kill_pids: verified all processes pids have been terminated {}'.format(pids))
            return isproc


def pidkill(pid, sig=0):
    """sends a signal to a process returns True if the pid is dead with no signal argument, sends no signal"""
    # if 'ps --no-headers' returns no lines, the pid is dead
    try:
        if sig == 0:
            log.debug('pidkill: sending signal 0 to check process status')
        else:
            log.debug('pidkill: killing process pid [{}] with signal {}'.format(pid, Signals(sig).name))
        return os.kill(pid, sig)
    except OSError as e:
        # process is dead
                if e.errno == 3:
                        log.debug('pidkill: process pid [{}] is already dead'.format(pid))
                        return True
        # no permissions
                elif e.errno == 1:
                        log.error('pidkill: failed killing process pid [{}], permission denied'.format(pid))
                        return False
                else:
                        raise


def piddead(pid):
    if pidkill(pid):
        return True
        # maybe the pid is a zombie that needs us to wait4 it
    try:
        log.debug('piddead: checking process pid [{}]'.format(pid))
        dead = os.waitpid(pid, os.WNOHANG)[0]
    except OSError as e:
        # pid is not a child
        if e.errno == 10:
            log.debug('piddead: process pid [{}] is not a child'.format(pid))
            return False
        else:
            raise
    return dead
# def kill(pid, sig=0): pass #DEBUG: test hang condition


def pidkill_gracefully(pid, interval=1, hung=5):
    """let process die gracefully, gradually send harsher signals if necessary"""
    for signal in [SIGTERM, SIGINT, SIGHUP, SIGKILL]:
        if pidkill(pid, signal):
            return True
        if piddead(pid):
            return True
        time.sleep(interval)
    i = 0
    while True:
    # infinite-loop protection
        if i < hung:
            i += 1
        else:
            log.warning('pidkill_gracefully: process pid [{}] is hung. giving up kill.'.format(pid))
            return False
    if pidkill(pid, SIGKILL):
        return True
    if piddead(pid):
        return True
    time.sleep(interval)
