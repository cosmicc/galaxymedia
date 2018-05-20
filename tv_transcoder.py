#!/usr/bin/python3.6
"""
 Galaxymedia TV Episode Transcoder

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
__progname__ = "tv_transcoder"
__description__ = "Galaxymedia TV Episode Transcoder"
__detaildesc__ = "Settings in config file /etc/galaxymediatools.cfg"

log = logging.getLogger()
parser = argparse.ArgumentParser(prog=__progname__, description=__description__, epilog=__detaildesc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
parser.add_argument('--debug', action='store_true', help='Debug mode logging to console')
args = parser.parse_args()
log.setLevel(logging.INFO)
if args.debug is True:
    log.setLevel(logging.DEBUG)
    console_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
    log_console = logging.StreamHandler()
    log.addHandler(log_console)
    log_console.setFormatter(console_format)
log_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
log_fileh = logging.FileHandler(cfg.config.get('logs', 'tv_transcoder'))
log.addHandler(log_fileh)
log_fileh.setFormatter(log_format)


def main():
    processlock.lock()
    log.debug('Starting Galaxymedia TV Transcoder')
    tv_dir = cfg.config.get('directories', 'tv_dir')
    daysback = int(cfg.config.get('general', 'tv_daysback'))
    log.debug(f'Compiling list of tv episodes to transcode on {tv_dir}')
    transvids = []
    numvids = 0
    days_ago = datetime.now() - timedelta(days=daysback)
    for (root, dirs, files) in os.walk(tv_dir):
        for file_ in files:
            videofile = os.path.join(root, file_)
            filetime = datetime.fromtimestamp(os.path.getctime(videofile))
            if not is_trans(videofile) and not is_tv_excluded(videofile) and os.path.getsize(videofile) > 1000000000 \
            and filetime < days_ago:
                transvids.append(videofile)
                numvids += 1
                log.debug(f'Added video {file_name(videofile)} to transcode list')
    log.info(f'Transcode list is complete with {numvids} episodes')
    for vid in transvids:
        log.debug(f'Determining ffmpeg settings for video {file_name(vid)}')
        vinfo = video_info(vid)
        ffmpeg_opstring = ''
        if vinfo['stream0']['codec_type'] != 'video':
            log.error(f'Stream0 in video file is not a video stream. Exiting.')
        if vinfo['stream0']["height"] == "na" or not vinfo['stream0']["height"]:
            log.error(f'Could not determine height of video stream. Exiting')
        if int(vinfo['stream0']["height"]) > 730:
            ffmpeg_opstring = ffmpeg_opstring + '-vf scale=1280:720 '
        ffmpeg_opstring = ffmpeg_opstring + f'-sn -c:v libx265 -preset ultrafast -x265-params \
        crf=20:qcomp=0.8:aq-mode=1:aq_strength=1.0:qg-size=16:psy-rd=0.7:psy-rdoq=5.0:rdoq-level=1:merange=44 \
        -c:a aac -ac 2'
        video_transcode(vid, ffmpeg_opstring)
    log.info('Galaxymedia TV Transcoder script complete.')


if __name__ == '__main__':
    main()
