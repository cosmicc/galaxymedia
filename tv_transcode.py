#!/usr/bin/python3.6
"""
 server maintenance script

"""
import os
import logging
import argparse
from datetime import datetime, timedelta

from modules.galaxymediamod import *
import modules.loadconfig as cfg
import modules.processlock as processlock

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"
__progname__ = "tv_transcode"
__description__ = "Galaxymedia TV show transcoder"
__detaildesc__ = ""

log = logging.getLogger()
parser = argparse.ArgumentParser(prog=__progname__, description=__description__, epilog=__detaildesc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
logging_group = parser.add_mutually_exclusive_group(required=False)
logging_group.add_argument('-q', '--quiet', action='store_false', help='supress normal console output')
logging_group.add_argument('--debug', action='store_true', help='Debug mode logging to console')
parser.add_argument('-v', '--verbose', action='count', help='logging verbosity level')
parser.add_argument('-l', '--logfile', help='log output to a specified file. default: no log to file')
args = parser.parse_args()
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


def main():
    processlock.lock()
    log.debug('Starting Galaxymedia TV Transcoder')
    tv_dir = cfg.config.get('directories', 'tv_dir')
    daysback = int(cfg.config.get('general', 'tv_daysback'))
    log.info(f'Compiling list of tv episodes to transcode on {tv_dir}')
    transvids = []
    numvids = 0
    days_ago = datetime.now() - timedelta(days=daysback)
    for (root, dirs, files) in os.walk(tv_dir):
        for file_ in files:
            videofile = os.path.join(root, file_)
            filetime = datetime.fromtimestamp(os.path.getctime(videofile))
            if not is_trans(videofile) and not is_tv_excluded(videofile) and os.path.getsize(videofile) > 300000000 \
            and filetime < days_ago:
                transvids.append(videofile)
                numvids += 1
                log.debug(f'Added video {file_name(videofile)} to transcode list')
    log.info(f'Transcode list is complete with {numvids} episodes')
    for vid in transvids:
        log.info(f'Determining ffmpeg settings for video {file_name(vid)}')
        vinfo = video_info(vid)
        ffmpeg_opstring = f'-i {in_file}'



if __name__ == '__main__':
    main()
