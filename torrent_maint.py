#!/usr/bin/python2
"""
 Deluge Torrent Maintenance Script

 Removes private torrents over ratio and expire time, removes all other finished torrents
"""
import sys
from datetime import datetime, timedelta
import logging
import argparse
from urlparse import urlparse
from configparser import ConfigParser

import publicsuffix

sys.path.insert(0, 'modules')
import processlock
from pushover2 import pushover
sys.path.insert(0, '/opt/deluge_framework')
from deluge_framework import filter_torrents

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"
__progname__ = "torrent_maintenance"
__description__ = "Galaxy deluge torrent maintenance tool"
__detaildesc__ = ""

configfile = '/etc/galaxymediatools.cfg'
config = ConfigParser()
config.read(configfile)

PROC_LABELS = ['tv', 'movies', 'ufc', 'comedy', 'files', 'music']  # torrent labels that will process
PROC_DIRS = PROC_LABELS
PRIV_TRACKERS = ['iptorrents.com', 'pleasuredome.org.uk', 'empirehost.me', 'stackoverflow.tech']  # trackers that are considered private

app_key = config.get('pushover', 'download_key')

log = logging.getLogger()
parser = argparse.ArgumentParser(prog=__progname__, description=__description__, epilog=__detaildesc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('action_to_perform', action='store', choices=['private', 'ratio', 'seedtime',
                                                                  'public', 'stale', 'nzbtomedia', 'totals',
                                                                  'pushtotals'], help='Action to perform')
action_group = parser.add_argument_group(title='actions')
action_group.add_argument('private', action='store_true', help='List all completed private torrents and totals')
action_group.add_argument('ratio', action='store_true', help='List all private torrents over the ratio specified')
action_group.add_argument('seedtime', action='store_true', help='List all private torrents over the seeded time')
action_group.add_argument('public', action='store_true', help='List all public torrents that are completed')
action_group.add_argument('stale', action='store_true', help='List all stale public torrents that are not downloading')
action_group.add_argument('checkstall', action='store_true', help='Check if deluge has stalled and all downloads stopped.  restarts vpn.')
action_group.add_argument('totals', action='store_true', help='Totals for listed torrents. used with -c option')
action_group.add_argument('nzbtomedia', action='store_true', help='Execute nzbToMedia for a specific category. used with -c option')
parser.add_argument('-c', '--category', nargs='?', action='store', default='all', choices=['tv','movies','comedy','ufc','concerts','games','files'], help='Filter by torrent category label (Default: all)')
parser.add_argument('-r', '--ratio', dest='RATIO', nargs='?', action='store', default=1.5, type=float, help='Ratio for private torrent list (Default: 1.5)')
parser.add_argument('-s', '--seeddays', dest='DELDAYS', nargs='?', action='store', default=15, type=int, help='Seeded timelimit for private torrent list in days (Default: 15)')
parser.add_argument('--delete', action='store_true', help='Delete listed torrents, instead of just displaying')
logging_group = parser.add_mutually_exclusive_group(required=False)
logging_group.add_argument('-q', '--quiet', action='store_false', help='supress normal console output')
logging_group.add_argument('--debug', action='store_true', help='Debug mode logging to console')
parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
parser.add_argument('-v', '--verbose', action='count', help='logging verbosity level')
parser.add_argument('-l', '--logfile', help='logging to a specified file. default: no log to file')
args = parser.parse_args()

mlog = log.getChild('deluge_framework')
mlog.setLevel(logging.WARNING)
if args.debug is True:
    console_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
    log_console = logging.StreamHandler()
    log.addHandler(log_console)
    log_console.setFormatter(console_format)
if args.logfile is not None:
    log_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
    log_fileh = logging.FileHandler(args.logfile)
    log.addHandler(log_fileh)
    log_fileh.setFormatter(log_format)
if args.debug is False and args.logfile is None:
    log.addHandler(logging.NullHandler())
if args.verbose:
    if args.verbose == 1:
        log.setLevel(logging.WARNING)
    elif args.verbose == 2:
        log.setLevel(logging.INFO)
    elif args.verbose >= 3:
        log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.ERROR)

processlock.lock()

sizetotal = 0
counttotal = 0
seedcount = 0
dlcount = 0
queuecount = 0
activecount = 0
pausecount = 0


def elapsedHours(stop_time, start_time):
    diff_time = stop_time - start_time
    total_secs = diff_time.seconds
    log.debug('Converted times to elapsed hours [{}] and [{}] to {} Hours'.format(start_time,stop_time,total_secs / 60 / 60))
    return((total_secs/60/60)+(diff_time.days*24))

def elapsedTime(start_time, stop_time, lshort=False):
    diff_time = stop_time - start_time
    days = diff_time.days
    if days == 1:
        daystring = 'Day'
    else:
        daystring = 'Days'
    total_secs = diff_time.seconds
    seconds = total_secs % 60
    if seconds == 1:
        if lshort is False:
            secstring = 'Second'
        else:
            secstring = 'Sec'
    else:
        if lshort is False:
            secstring = 'Seconds'
        else:
            secstring = 'Secs'
    total_min = total_secs / 60
    minutes = int(total_min % 60)
    if minutes == 1:
        if lshort is False:
            minstring = 'Minute'
        else:
            minstring = 'Min'
    else:
        if lshort is False:
            minstring = 'Minutes'
        else:
            minstring = 'Mins'
    hours = int(total_min / 60)
    if hours == 1:
        if lshort is False:
            hourstring = 'Hour'
        else:
            hourstring = 'Hr'
    else:
        if lshort is False:
            hourstring = 'Hours'
        else:
            hourstring = 'Hrs'
    if days != 0:
        return('{} {}, {} {}, {} {}'.format(days, daystring, hours, hourstring, minutes, minstring))
    elif hours != 0:
        return('{} {}, {} {}'.format(hours, hourstring, minutes, minstring))
    elif minutes != 0:
        return('{} {}, {} {}'.format(minutes, minstring, seconds, secstring))
    elif minutes == 0:
        return('{} {}'.format(seconds, secstring))
    else:
        log.error('Elapsed time function failed. Could not convert.')
        return('Error')


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


def trunc_tracker(rawtracker):
    urlres = urlparse(rawtracker)
    urlinfo = (urlres.netloc.split(":"))
    if urlinfo[0] == '':
        return 'NONE'
    else:
        domainret = publicsuffix.PublicSuffixList().get_public_suffix(urlinfo[0])
        log.debug('trunc_tracker returning domain name {} from string {}'.format(domainret,rawtracker))
        return domainret


def stale_action(torrent_id,torrent_info):
    traptorrent = False
    if trunc_tracker(torrent_info['tracker']) not in PRIV_TRACKERS and torrent_info['progress'] != 100 and torrent_info['download_payload_rate'] == 0:
        if torrent_info['label'] in PROC_LABELS and torrent_info['total_seeds'] < 5:
            if torrent_info['state'] == 'Downloading':
                torrent_hours = elapsedHours(datetime.now(),datestring2object(torrent_info['time_added']))
                if torrent_hours > 240 and torrent_info['progress'] < 90:
                    traptorrent = True
                if torrent_hours > 48 and torrent_info['progress'] < 20:
                    traptorrent = True
                if torrent_hours > 24 and torrent_info['progress'] < 5:
                    traptorrent = True
        if traptorrent is True:
            log.debug('label: {} progress: {} num_seeds: {} total_seeds: {} dl_rate: {} elapsed hours: {}'
                      .format(torrent_info['label'], torrent_info['progress'], torrent_info['num_seeds'],
                              torrent_info['total_seeds'], torrent_info['download_payload_rate'], torrent_hours))
            if args.delete is True:
                log.warning('Deleting stale torrent {}'.format(torrent_info['name']))
                # THIS IS WHERE NZBTOMEDIA NEEDS TO REPORT THE TORRENT AS FAILED TO THE CORRECT MEDIA MANAGER ########    
                return 'D'
            else:
                log.info('Stale public torrent found {}'.format(torrent_info['name']))
                return 'l'
    return ''

def stale_torrents():
    filter_torrents({}, ['name', 'label', 'time_added', 'state', 'progress', 'num_seeds', 'download_payload_rate',
                         'total_seeds', 'tracker'], stale_action, args.quiet)


def checkstall_action(torrent_id,torrent_info):
    if trunc_tracker(torrent_info['tracker']) not in PRIV_TRACKERS and torrent_info['progress'] != 100:
        if torrent_info['label'] in PROC_LABELS and torrent_info['state'] == 'Downloading' and torrent_info['progress'] < 20:
            torrent_hours = elapsedHours(datetime.now(), datestring2object(torrent_info['time_added']))
            if torrent_hours > 48 and torrent_info['download_payload_rate'] == 0 and torrent_info['total_seeds'] < 5:
                log.debug('label: {} progress: {} num_seeds: {} total_seeds: {} dl_rate: {} elapsed hours: {}'
                          .format(torrent_info['label'], torrent_info['progress'], torrent_info['num_seeds'],
                                  torrent_info['total_seeds'], torrent_info['download_payload_rate'], torrent_hours))
                if args.delete is True:
                    log.warning('Deleting stale torrent {}'.format(torrent_info['name']))
                    return 'D'
                else:
                    log.info('Stale public torrent found {}'.format(torrent_info['name']))
                    return 'l'
    return ''


def checkstall_torrents():
        filter_torrents({}, ['name', 'label', 'time_added', 'state', 'progress', 'num_seeds', 'download_payload_rate', 
                             'total_seeds', 'tracker'], checkstall_action, args.quiet)

def totals_action(torrent_id, torrent_info):
    global sizetotal
    global counttotal
    global seedcount
    global dlcount
    global queuecount
    global activecount
    global pausecount
    if args.category == 'all' or args.category == torrent_info['label']:
        counttotal += 1
        sizetotal += torrent_info['total_done']
        if torrent_info['download_payload_rate'] != 0:
            activecount += 1
        if torrent_info['state'] == 'Paused':
            pausecount += 1
        elif torrent_info['state'] == 'Downloading':
            dlcount += 1
        elif torrent_info['state'] == 'Queued':
            queuecount += 1
        elif torrent_info['state'] == 'Seeding':
            seedcount += 1
        return 'l'
    return ''


def totals_torrents(notify=False):
    filter_torrents({}, ['name', 'label', 'total_done', 'state', 'download_payload_rate', 'progress'],
                    totals_action, args.quiet)
    sizegigs = sizetotal/1024/1024/1024
    if notify is True:
        pushover(app_key, 'Download Statistics', 'Total Torrents: {}\nTotal Torrent Size: {} Gigs\nDownloading:'
                 ' {}\nActive Downloading: {}\nQueued: {}\nSeeding: {}\nPaused: {}'
                 .format(counttotal, sizegigs, dlcount, activecount, queuecount, seedcount, pausecount))
    else:
        print('Listing torrent for category: [{}]'.format(args.category))
        print('Total size of {} torrents listed: {} Gigs'.format(counttotal,sizegigs))
        print('Total torrents in state [Downloading]: {}'.format(dlcount))
        print('Total torrents in state [Active Downloading]: {}'.format(activecount))
        print('Total torrents in state [Queued]: {}'.format(queuecount))
        print('Total torrents in state [Paused]: {}'.format(pausecount))
        print('Total torrents in state [Seeding]: {}'.format(seedcount))
        log.info('Total torrents {} and size of all torrents [{}] Gig'.format(counttotal,sizegigs))
        # return [sizetotal/1024/1024/1024,tcount]


def finishedpub_action(torrent_id, torrent_info):
    if trunc_tracker(torrent_info['tracker']) not in PRIV_TRACKERS and \
     torrent_info['progress'] == 100 and torrent_info['label'] in PROC_LABELS:
        if torrent_info['state'] == 'Seeding' or torrent_info['state'] == 'Paused':
            log.info('tracker: {} public completed torrent found to delete {}'.format(trunc_tracker(torrent_info['tracker']),torrent_info['name']))
            if args.delete is True:
                log.warning('tracker: {} deleting public completed torrent {}'.format(trunc_tracker(torrent_info['tracker']),torrent_info['name']))
                return 'D'
            else:
                log.info('tracker: {} public completed torrent found {}'.format(trunc_tracker(torrent_info['tracker']),torrent_info['name']))
                return 'l'
    return ''


def finished_public_torrents():
    filter_torrents({}, ['name', 'tracker', 'save_path', 'progress', 'state', 'time_added', 'label'],
                    finishedpub_action, args.quiet)


def overtime_action(torrent_id, torrent_info):
    if trunc_tracker(torrent_info['tracker']) in PRIV_TRACKERS and torrent_info['progress'] == 100 and torrent_info['label'] in PROC_LABELS:
        curtime = datetime.now()
        seedtime = datestring2object(torrent_info["time_added"])
        if curtime > seedtime + timedelta(days=args.DELDAYS):
            if args.delete is True:
                log.warning('deleting private torrent over seed time limit of {} Days: {} - {}'
                            .format(args.DELDAYS,elapsedTime(seedtime, curtime),torrent_info['name']))
                return 'D'
            else:
                log.info('private torrent found over seed time limit of {} Days: {} - {}'
                         .format(args.DELDAYS,elapsedTime(seedtime,curtime),torrent_info['name']))
                return 'l'
    return ''


def torrents_over_timelimit():
    filter_torrents({}, ['name', 'time_added', 'save_path', 'label', 'tracker', 'progress'],
                    overtime_action, args.quiet)


def overratio_action(torrent_id,torrent_info):
    if trunc_tracker(torrent_info['tracker']) in PRIV_TRACKERS and torrent_info['progress'] == 100 and torrent_info['label'] in PROC_LABELS:
        if torrent_info['ratio'] > args.RATIO:
            if args.delete is True:
                log.warning('deleting private torrent over seed ratio of {}>{} - {}'
                            .format(float_trunc_2dec(torrent_info['ratio']),args.RATIO,torrent_info['name']))
                return 'D'
            else:
                log.info('private torrent found over seed ratio of {}>{} - {}'.format(float_trunc_2dec(torrent_info['ratio']),args.RATIO,torrent_info['name']))
                return 'l'
    return ''

def torrents_over_ratio():
    filter_torrents({},['name','ratio','progress','save_path', 'label', 'tracker'],overratio_action,args.quiet)


#----
log.debug('starting script')

if args.action_to_perform == 'totals':
    log.debug('checking torrent totals for the {} category'.format(args.category))
    totals_torrents()
    exit()

if args.action_to_perform == 'pushtotals':
    log.debug('pushover notifying torrent totals'.format(args.category))
    totals_torrents(True)
    exit()

if args.action_to_perform == 'stale':
    log.debug('checking for stale public torrents')
    stale_torrents()
    exit()

if args.action_to_perform == 'chekstall':
    log.debug('checking for staler public torrents')
    checkstall_torrents()
    exit()

if args.action_to_perform == 'public':
   log.info('checking for finished public torrents to delete')
   finished_public_torrents()

if args.action_to_perform == 'ratio':
    log.info('checking for over ratio torrents to delete')
    torrents_over_ratio()

if args.action_to_perform == 'seedtime':
    log.info('checking for over seeded timelimit torrents to delete')
    torrents_over_timelimit()

if args.action_to_perform == 'nzbtomedia':
    if args.category:
        log.info('executing nzbtomedia for category {}'.format(args.category))
        processMedia(args.category)
    else:
        log.critical('Category not specified for nzbToMedia script')
        print('Category required for nzbToMedia script. -c option')


