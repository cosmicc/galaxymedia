#!/usr/bin/python3.6
"""
 server maintenance script

"""
import sys
import os
import logging
import argparse

from colorama import Fore, Back, Style

from modules.galaxymediamod import *
import modules.loadconfig as cfg
import modules.processlock as processlock

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"
__progname__ = "videoinfo"
__description__ = "Prints information about a video file"
__detaildesc__ = ""

log = logging.getLogger()
parser = argparse.ArgumentParser(prog=__progname__, description=__description__, epilog=__detaildesc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
parser.add_argument('--debug', action='store_true', help='Debug mode logging to console')
parser.add_argument('-r', '--raw', action='store_true', help='Include raw video info')
parser.add_argument('video_file', action='store', help='video file to process')
args = parser.parse_args()
if args.debug is True:
    console_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
    log_console = logging.StreamHandler()
    log.addHandler(log_console)
    log_console.setFormatter(console_format)
    log.setLevel(logging.ERROR)

YEL = Fore.YELLOW
CYN = Fore.CYAN
WHT = Fore.WHITE
MGT = Fore.MAGENTA
GRN = Fore.GREEN
RST = Fore.RESET

def print_stream(vinfo, stream):
    print(f'{CYN}[{YEL}Stream {int(stream+1)}{CYN}]')
    print(f'{CYN}Codec Type: {YEL}{vinfo[f"stream{stream}"]["codec_type"].capitalize()}')
    if vinfo[f"stream{stream}"]["codec_type"] != "data":
        print(f'{CYN}Codec Name: {YEL}{vinfo[f"stream{stream}"]["codec_name_long"]}')
    if vinfo[f"stream{stream}"]["codec_type"] == "video":
        if int(vinfo["stream0"]['width']) < 1290 and int(vinfo["stream0"]['width']) > 1270:
            vmode = ' [720p]'
        elif int(vinfo["stream0"]['width']) < 1930 and int(vinfo["stream0"]['width']) > 1910:
            vmode = ' [1080p]'
        elif int(vinfo["stream0"]['width']) < 3850 and int(vinfo["stream0"]['width']) > 3830:
            vmode = ' [4k]'
        else:
            vmode = ''
        print(f'{CYN}Resolution: {YEL}{vinfo[f"stream{stream}"]["width"]}{GRN}x{YEL}{vinfo[f"stream{stream}"]["height"]}{GRN}{vmode}')
        print(f'{CYN}Video Bit Rate: {YEL}{format_size(vinfo[f"stream{stream}"]["bit_rate"])}')
        print(f'{CYN}Aspect Ratio: {YEL}{vinfo[f"stream{stream}"]["aspect_ratio"]}')
        print(f'{CYN}Level: {YEL}{vinfo[f"stream{stream}"]["level"]}')
    elif vinfo[f"stream{stream}"]["codec_type"] == "audio":
        print(f'{CYN}Audio Bit Rate: {YEL}{format_size(vinfo[f"stream{stream}"]["bit_rate"])}')
        print(f'{CYN}Sample Rate: {YEL}{vinfo[f"stream{stream}"]["sample_rate"]}')
        print(f'{CYN}Audio Channels: {YEL}{vinfo[f"stream{stream}"]["channels"]}')
        print(f'{CYN}Channel Layout: {YEL}{vinfo[f"stream{stream}"]["channel_layout"]}')
        print(f'{CYN}Language: {YEL}{vinfo[f"stream{stream}"]["language"].upper()}')
    elif vinfo[f"stream{stream}"]["codec_type"] == "subtitle":
        print(f'{CYN}Title: {YEL}{vinfo[f"stream{stream}"]["title"]}')
        print(f'{CYN}Language: {YEL}{vinfo[f"stream{stream}"]["language"].upper()}')


def main():
    processlock.lock()
    in_file = os.path.abspath(args.video_file)
    if not os.path.isfile(in_file):
        log.error(f'File does not exist. {in_file}')
        exit(1)
    if args.raw:
        vinfo = video_info(in_file,raw=True)
    else:
        vinfo = video_info(in_file)
    print(f'{GRN}Galaxy Media Video File Information:\n')
    print(f'{CYN}Raw: {YEL}{in_file}')
    print(f'{CYN}Directory: {YEL}{file_dir(in_file)}')
    print(f'{CYN}Filename: {YEL}{file_name(in_file)}')
    print(f'{CYN}Name: {YEL}{file_name_noext(in_file)}')
    print(f'{CYN}Extension: {YEL}{file_ext(in_file).upper()}')
    print(f'{CYN}Format: {YEL}{vinfo["format_long"]}')
    print(f'{CYN}Streams: {YEL}{vinfo["streams"]}')
    print(f'{CYN}Duration: {YEL}{vinfo["duration"]}')
    print(f'{CYN}Total Bit Rate: {YEL}{format_size(vinfo["bit_rate"])}')
    print(f'{CYN}File Size: {YEL}{format_size(os.path.getsize(in_file))}')
    for stream in range(int(vinfo["streams"])):
        print(' ')
        print_stream(vinfo, stream)
    print(f'{RST}')

if __name__ == '__main__':
    main()
