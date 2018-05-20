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
parser.add_argument('file', action='store', help='file to process')
args = parser.parse_args()
if args.debug is True:
    console_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
    log_console = logging.StreamHandler()
    log.addHandler(log_console)
    log_console.setFormatter(console_format)
    log.setLevel(logging.ERROR)


def main():
    processlock.lock()
    in_file = sys.argv[1]
    YEL = Fore.YELLOW
    CYN = Fore.CYAN
    WHT = Fore.MAGENTA
    RST = Fore.RESET
    if not os.path.isfile(in_file):
        log.error(f'File does not exist. {in_file}')
        exit(1)
    vinfo = video_info(in_file)
    print(f'{WHT}Galaxy Media Video File Information:\n')
    print(f'{CYN}Filename: {YEL}{file_name_noext(in_file)}')
    print(f'{CYN}Extension: {YEL}{file_ext(in_file)}\n')
    print(f'{CYN}Format: {YEL}{


    print(f'{RST}')

if __name__ == '__main__':
    main()
