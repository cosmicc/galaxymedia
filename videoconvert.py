#!/usr/bin/python3.6
"""
 server maintenance script

"""
import logging
import argparse
import subprocess
import json

from colorama import Fore, Back, Style
import ffmpy

import modules.loadconfig as cfg
import modules.processlock as processlock

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"
__progname__ = "videoconvert"
__description__ = "Galaxy deluge torrent maintenance tool"
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
parser.add_argument('file', action='store', help='file to process')
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
    print('This is is {}fantastic {}colors{}'.format(Fore.YELLOW, Fore.CYAN, Fore.RESET))
    ffprobe = ffmpy.FFprobe(global_options=("-loglevel quiet -sexagesimal -of json -show_format -show_streams", args.file))
    print(f"ffprobe.cmd: {ffprobe.cmd}")  # printout the resulting ffprobe shell command
    stdout, stderr = ffprobe.run(stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    # std* is byte sequence, but json in Python 3.5.2 requires str
    ff0string = str(stdout, 'utf-8')

    ffinfo = json.loads(ff0string)
    print(json.dumps(ffinfo, indent=4))  # pretty print

    print("Format Name: ", ffinfo["format"]["format_name"])
    print("Streams: ", ffinfo["format"]["nb_streams"])
    for stream in range(ffinfo["format"]["nb_streams"]):
        print(f'Codec Type: {ffinfo["streams"][stream]["codec_type"]}', end='')
        print(f' Name: {ffinfo["streams"][stream]["codec_name"]}', end='')
        if ffinfo["streams"][stream]["codec_type"] == 'video':
            print(f' Size: {ffinfo["streams"][stream]["width"]}', end='')
            print(f'x{ffinfo["streams"][stream]["height"]}')
        if ffinfo["streams"][stream]["codec_type"] == 'audio':
            print(f' Channels: {ffinfo["streams"][stream]["channels"]}', end='')
   #        print(f' Language: {ffinfo["streams"][stream]["tags"]["language"]}', end='')
        print('\n')


if __name__ == '__main__':
    main()
