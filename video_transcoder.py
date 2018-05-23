#!/usr/bin/python3.6
"""
 video transcoder

"""
import os
import logging
import argparse

from colorama import Fore, Back, Style
import daemon

import modules.loadconfig as cfg
import modules.processlock as processlock
from modules.galaxymediamod import *

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
logging_group.add_argument('-q', '--quiet', action='store_true', help='supress normal console output')
logging_group.add_argument('--debug', action='store_true', help='Debug mode logging to console')
parser.add_argument('-r', '--replace', action='store_true', help='Replace original video file')
parser.add_argument('video_file', action='store', help='Video file or directory to transcode')
video_group = parser.add_argument_group('Video Options')
video_group.add_argument('-h265', action='store_true', help='Convert video to HEVC h265')
video_group.add_argument('-2pass', action='store_true', help='Use 2 Pass h265 encoding (1 Pass default)')
video_group.add_argument('-r720', action='store_true', help='Resize video to 720p')
video_group.add_argument('-r1080', action='store_true', help='Resize video to 1080p')
video_group.add_argument('-level', action='store', default=21, help='h265 Quality level [0-51] 0=lossless 21=default')
video_group.add_argument('-speed', action='store', default='ultrafast', choices=["ultrafast", "superfast", "veryfast", "faster", "fast", \
        "medium", "slow", "slower", "veryslow"], help='Encoding speed (Affects overall quality) ultrafast=default')
audio_group = parser.add_argument_group('Audio Options')
audio_group.add_argument('-aac', action='store_true', help='Convert audio to AAC 2 channel')
subtitle_group = parser.add_argument_group('Subtitle Options')
subtitle_group.add_argument('-nosubs', action='store_true', help='Remove subtitles from video')
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

#pdict = {'ultrafast': 0, 'superfast': 1, 'veryfast': 2, 'faster': 3, 'fast': 4, 'medium': 5, \
#         'slow': 6, 'slower': 7, 'veryslow': 8}

YEL = Fore.YELLOW
CYN = Fore.CYAN
WHT = Fore.WHITE
MGT = Fore.MAGENTA
GRN = Fore.GREEN
RED = Fore.RED
RST = Fore.RESET


def main():
    processlock.lock()
    if args.video_file == '.' or os.path.isdir(args.video_file):
        vdir = os.path.abspath(args.video_file)
        for vfile in os.listdir(vdir):
            proc_vid(vfile)
    else:
        proc_vid(args.video_file)

def proc_vid(in_file):
    in_file = os.path.abspath(args.video_file)
    vinfo = video_info(in_file)
    duration = f'{YEL}{vinfo["duration"]}{RST}'
    vbitrate = f'{YEL}{format_size(int(vinfo["bit_rate"]))}{RST}'
    for stream in range(int(vinfo['streams'])):
        if vinfo[f"stream{stream}"]["codec_type"] == "video":
            ctype = f'{YEL}{vinfo[f"stream{stream}"]["codec_name"]}{RST}'
            if int(vinfo[f"stream{stream}"]['width']) < 1290 and int(vinfo[f"stream{stream}"]['width']) > 1270:
                vmode = f'{GRN}[720p]{RST}'
            elif int(vinfo[f"stream{stream}"]['width']) < 1930 and int(vinfo[f"stream{stream}"]['width']) > 1910:
                vmode = f'{GRN}[1080p]{RST}'
            elif int(vinfo[f"stream{stream}"]['width']) < 3850 and int(vinfo[f"stream{stream}"]['width']) > 3830:
                vmode = f'{GRN}[4k]{RST}'
            else:
                vmode = ''
            resolution = f'{YEL}{vinfo[f"stream{stream}"]["width"]}{GRN}x{YEL}{vinfo[f"stream{stream}"]["height"]} {vmode}{RST} '
        if vinfo[f"stream{stream}"]["codec_type"] == "audio":
            atype = f'{YEL}{vinfo[f"stream{stream}"]["codec_name"]} {vinfo[f"stream{stream}"]["channels"]}ch{RST}'

    if args.r720 and args.r1080:
        log.error('You can not specify 720p and 1080p resize at the same time. Exiting.')
        print('You can not specify 720p and 1080p resize at the same time. Exiting.')
        exit(1)
    if not os.path.isfile(in_file):
        log.error(f'Video file does not exist. Exiting. [{in_file}]')
        print(f'Video file does not exist. Exiting. [{in_file}]')
        exit(1)
    # check to see if anything to do:
    if not args.h265 and not args.aac and not args.nosubs:
        log.error(f'No arguments. Nothing to do to video file. Exiting. [{in_file}]')
        print(f'No arguments. Nothing to do to video file. Exiting. [{in_file}]')
        exit(0)
    if not video_isinteg(in_file):
        log.error(f'Video file failed integrity check. Exiting. [{in_file}]')
        print(f'Video file failed integrity check. Exiting. [{in_file}]')
        exit(2)  # DO SOMETHING INSTEAD OF JUST EXITING
    if is_trans(in_file):
        log.warning(f'Video file is already marked transcoded. [{in_file}]')
        print(f'Video file is already marked transcoded. [{in_file}]')
        return
    if args.quiet:
        ffmpegss = f'-nostats -hide_banner '
    else:
        ffmpegss = ''
    # VIDEO OPTIONS
    if args.r720:
        ffmpegss = f'{ffmpegss}-vf scale=1280:720 '
    elif args.r1080:
        ffmpegss = f'{ffmpegss}-vf scale=1920:1080 '
    if not args.h265 or args.h265 is None:
        ffmpegss = f'{ffmpegss}-c:v copy '
    else:
        x265parms = f'crf={args.level}:'
        x265parms = f'{x265parms}qcomp=0.8:aq-mode=1:aq_strength=1.0:qg-size=16:psy-rd=0.7:psy-rdoq=5.0:rdoq-level=1:merange=44:log-level=0'
        ffmpegss = f'{ffmpegss}-c:v libx265 -preset {args.speed} -x265-params {x265parms} '
    # AUDIO OPTIONS
    if not args.aac or args.aac is None:
        ffmpegss = f'{ffmpegss}-c:a copy '
    else:
        ffmpegss = f'{ffmpegss}-c:a aac -ac 2 '
    if args.nosubs:
        ffmpegss = f'{ffmpegss}-sn '
    print(f'{GRN}Galaxymedia HEVC h265 video transcoder{RST}\n')
    print(f'{CYN}Video: {YEL}{in_file}{RST}')
    print(f'{CYN}FFmpeg Options: {YEL}{ffmpegss}{RST}')
    print(f'{CYN}Replacing original video file: {YEL}{args.replace}{RST}\n')
    print(f'{CYN}Video: {ctype} {CYN}Resolution: {resolution} {CYN}Duration: {duration} {CYN}Bitrate: {vbitrate} {CYN}Audio: {atype}\n')
    if args.replace:
        tresult = video_transcode(in_file, ffmpegss, console=True)
    else:
        tresult = video_transcode(in_file, ffmpegss, norep=True, console=True)
    if tresult:
        log.info(f'Transcode Successful. {file_name(in_file)}\n')
        print(f'{GRN}Transcode Successful. {CYN}[{YEL}{file_name(in_file)}{CYN}]{RST}\n')
    else:
        log.info(f'Transcode Warnings/Errors. {file_name(in_file)}\n')
        print(f'{RED}Transcode Warnings/Errors. {CYN}[{YEL}{file_name(in_file)}{CYN}]{RST}\n')

if __name__ == '__main__':
    main()
