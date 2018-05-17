#!/usr/bin/python3.6
"""
 fuctions used in galaxymedia scripts

"""

import os
import subprocess
import logging
from urllib.request import urlopen
from urllib.parse import urlparse
from datetime import datetime

from configparser import ConfigParser
import publicsuffix
from pexpect import pxssh
from wakeonlan import send_magic_packet as wol

import modules.loadconfig as cfg
from modules.pushover import Client

log = logging.getLogger()

categories = {'movies': cfg.get('plex', 'movie_section'), 'tv': cfg.get('plex', 'tv_section'), 'comedy': cfg.get('plex', 'comedy_section'), 'ufc': cfg.get('plex', 'ufc_section')}
plextoken = cfg.get('plex', 'token')


def is_root():
    user = os.getenv("SUDO_USER")
    if user is None:
        return False
    else:
        return True


def require_root():
    user = os.getenv("SUDO_USER")
    if user is None:
        log.error("This program needs root privledges")
        exit(1)


def remote_cmd(server, username, password, cmd):
    ssh = pxssh.pxssh()
    try:
        ssh.login(server, username, password)
    except pxssh.ExceptionPexpect as e:
        print('Failed to connect to remote server with SSH')
        return False
    else:
        print('SSH connected to remote server [{}]'.format('server'))
        try:
            ssh.sendline(cmd)
            ssh.prompt()
            ssh.sendline('echo $?')
            ssh.prompt()
            splitres = ssh.before.decode().split('\r\n')
            result = splitres[1]
        except:
            print('SSH remote command execution failed')
            return False
        else:
            print('SSH remote command executed successfully')
            return result

def wakeup(macaddr):
    wol(macaddr)


def pushover(app_key, ptitle, message):
    try:
        client = Client(cfg.get('pushover', 'user_key'), api_token=app_key)
        client.send_message(message, title=ptitle)
    except Exception as e:
        log.error('Pushover notification failed. Error: %s' % str(e))
        return False
    else:
        log.debug('Pushover notification sent. Title: {}'.format(ptitle))
        return True

def processMedia(category):
    log.info('Executing nzbToMedia for category {}'.format(category))
    ourl = '/mnt/incoming/process/deluge/{}'.format(category)
    log.debug('url to open: {}'.format(ourl))
    try:
        subprocess.call(['/usr/local/nzbToMedia/nzbToMedia.py', ourl, '', category, '', 'generic'])
    except:
        log.exception('Error executing nzbToMedia script for category {}'.format(category))
    else:
        log.info('nzbToMedia executed successfully for category {}'.format(category))

def plex_updatesection(category):
    try:
        urlopen('http://172.25.1.26:32400/library/sections/{}/refresh?X-Plex-Token={}'.format(categories[category],plextoken))
    except:
        log.error('URL Error opening URL for plex section update')
    else:
        log.info('Updates plex section {} successfully'.format(category))

def elapsedHours(stop_time, start_time):
    diff_time = stop_time - start_time
    total_secs = diff_time.seconds
    log.debug('Converted times to elapsed hours [{}] and [{}] to {} Hours'.format(start_time,stop_time,total_secs / 60 / 60))
    return((total_secs/60/60)+(diff_time.days*24))

def elapsedTime(stop_time, start_time,lshort=False):
    log.debug('Converting times to elapsed time [{}] and [{}]'.format(start_time,stop_time))
    diff_time = stop_time - start_time
    days = diff_time.days
    if days == 1:
        daystring = 'Day'
    else:
        daystring = 'Days'
    total_secs = diff_time.seconds
    seconds = total_secs % 60
    if seconds == 1:
        if lshort == False:
            secstring = 'Second'
        else:
            secstring = 'Sec'
    else:
        if lshort == False:
            secstring = 'Seconds'
        else:
            secstring = 'Secs'
    total_min = total_secs / 60
    minutes = int(total_min % 60)
    if minutes == 1:
        if lshort == False:
            minstring = 'Minute'
        else:
            minstring = 'Min'
    else:
        if lshort == False:
            minstring = 'Minutes'
        else:
            minstring = 'Mins'
    hours = int(total_min / 60)
    if hours == 1:
        if lshort == False:
            hourstring = 'Hour'
        else:
            hourstring = 'Hr'
    else:
        if lshort == False:
            hourstring = 'Hours'
        else:
            hourstring = 'Hrs'
    if days != 0:
        log.debug('elapsedTime: {} {}, {} {}, {} {}'.format(days,daystring,hours,hourstring,minutes,minstring))
        return('{} {}, {} {}, {} {}'.format(days,daystring,hours,hourstring,minutes,minstring))
    elif hours != 0:
        log.debug('elapsedTime: {} {}, {} {}'.format(hours,hourstring,minutes,minstring))
        return('{} {}, {} {}'.format(hours,hourstring,minutes,minstring))
    elif minutes != 0:
        log.debug('elapsedTime: {} {}, {} {}'.format(minutes,minstring,seconds,secstring))
        return('{} {}, {} {}'.format(minutes,minstring,seconds,secstring))
    elif minutes == 0:
        log.debug('elapsedTime: {} {}'.format(seconds,secstring))
        return('{} {}'.format(seconds,secstring))
    else:
        log.error('Elapsed time function failed. Could not convert.')
        return('Error')

def float_trunc_2dec(num):
    try:
        tnum = num // 0.01 / 100
    except:
        log.exception('Error truncating float to 1 decimal: {}'.format(num))
        return False
    else:
        return tnum

def trunc_savepath(spath):
    savedir = spath.split('/')
    return savedir[-1]

def trunc_tracker(rawtracker):
    urlres = urlparse(rawtracker)
    urlinfo = (urlres.netloc.split(":"))
    if urlinfo[0] == '':
        return 'NONE'
    else:
        domainret = publicsuffix.PublicSuffixList().get_public_suffix(urlinfo[0])
        log.debug('trunc_tracker returning domain name {} from string {}'.format(domainret,rawtracker))
        return domainret

def datestring2object(datestring):
    if isinstance(datestring, datetime):
       log.debug('datestring is already datetime object, no conversion neded')
       return datestring
    elif isinstance(datestring, str):
       log.debug('datestring {} is string and converting to datetime object'.format(datestring))
       numunixtimea = int(datestring[:-2])
       return datetime.fromtimestamp(numunixtimea)
    elif isinstance(datestring, int):
       log.debug('datestring {} is int and converting to datetime object'.format(datestring))
       return datetime.fromtimestamp(datestring)
    elif isinstance(datestring, float):
       log.debug('datestring {} is float and converting to datetime object'.format(datestring))
       numunixtimea = int(datestring)
       log.debug(numunixtimea)
       return datetime.fromtimestamp(datestring)
    else:
       log.critical('datestring in unknown format, cannot convert')

def diskspace(path):
    if not os.path.exists(path):
        log.error('Invalid path specified for diskspace check: {}'.format(path))
    else:
        if not os.name == 'posix':
            log.error('Diskspace check only supports Linux/Unix environments')
        else:
            try:
                osstatvfs = os.statvfs(path)
                fsbytes = osstatvfs.f_frsize * osstatvfs.f_blocks     # Size of filesystem in bytes
                fsfree = osstatvfs.f_frsize * osstatvfs.f_bavail     # Number of free bytes that ordinary users
                fsmb = fsbytes / 1000000  # convert to MB
                fsmbfree = fsfree / 1000000  # convert to MB
                fskb = fsbytes / 1000
                fskbfree = fsfree / 1000
                fsgb = fsbytes / 1000000000
                fsgbfree = fsfree / 1000000000
            except:
                log.exception('Error while trying to determine disk space for {}'.format(path))
                return False
            else:
                fsreturn = {}
                fsreturn['GBfree'] = round(fsgbfree, 1)
                fsreturn['GBtotal'] = round(fsgb, 1)
                fsreturn['MBfree'] = round(fsmbfree, 1)
                fsreturn['MBtotal'] = round(fsmb, 1)
                fsreturn['KBfree'] = round(fskbfree, 1)
                fsreturn['KBtotal'] = round(fskb, 1)
                fsreturn['Bytesfree'] = round(fsfree, 1)
                fsreturn['Bytestotal'] = round(fsbytes, 1)
                return fsreturn
