#!/usr/bin/python3.6
"""
 video transcoder

"""
import os
import logging
import argparse

from colorama import Fore, Back, Style

import modules.loadconfig as cfg
import modules.processlock as processlock

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"
__progname__ = "video_transcoder"
__description__ = "Galaxymedia HEVC v265 video transcoder"
__detaildesc__ = ""

log = logging.getLogger()
parser = argparse.ArgumentParser(prog=__progname__, description=__description__, epilog=__detaildesc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
logging_group = parser.add_mutually_exclusive_group(required=False)
logging_group.add_argument('-q', '--quiet', action='store_false', help='supress normal console output')
logging_group.add_argument('--debug', action='store_true', help='Debug mode logging to console')
parser.add_argument('video_file', action='store', help='Video file to transcode')
video_group = parser.add_argument_group('Video Options')
video_group.add_argument('-h265', action='store_true', help='Convert video to HEVC h265')
video_group.add_argument('-2pass', action='store_true', help='Use 2 Pass h265 encoding (1 Pass default)')
video_group.add_argument('-720', action='store_true', help='Resize video to 720p')
video_group.add_argument('-1080', action='store_true', help='Resize video to 1080p')
video_group.add_argument('-level', action='store', help='h265 Quality level [0-51] 0=lossless 21=default')
video_group.add_argument('-speed', action='store', choices=[], help='Encoding speed (Affects overall quality) ultrafast=default')
parser.add_argument('-nosub', action='store_true', help='Remove subtitles from video')
parser.add_argument('-aac', action='store_true', help='Convert audio to AAC 2 channel')
parser.add_argument('-v', '--verbose', action='count', help='logging verbosity level')
parser.add_argument('-l', '--logfile', help='log output to a specified file. default: no log to file')
args = parser.parse_args()
if not args.debug and args.logfile is None:
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
if args.debug:
    log.setLevel(logging.DEBUG)
    console_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
    log_console = logging.StreamHandler()
    log.addHandler(log_console)
    log_console.setFormatter(console_format)
if args.logfile is not None:
    log_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
    log_fileh = logging.FileHandler(args.logfile)
    log.addHandler(log_fileh)
    log_fileh.setFormatter(log_format)


def main():
    processlock.lock()
    in_file = os.path.abspath(video_file)
    if not os.path.isfile(in_file):
        log.error(f'Video file does not exist. Exiting [{in_file}]')
        exit(1)
    if not video_isinteg(in_file):
        log.error(f'Video file failed integrity check. Exiting [{in_file}]')
        exit(2)


    ### CHECK IF VIDEO IS ALREADY H265
    print('This is is {}fantastic {}colors{}'.format(Fore.YELLOW, Fore.CYAN, Fore.RESET))


if __name__ == '__main__':
    main()
