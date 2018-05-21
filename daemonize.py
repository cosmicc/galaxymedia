#!/usr/bin/python3.6
"""
 python script daemonizer

"""
import os
import argparse
import subprocess

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"
__progname__ = "daemonize"
__description__ = "Python script daemonizing tool"
__detaildesc__ = "Runs a python script as a daemon"

parser = argparse.ArgumentParser(prog=__progname__, description=__description__, epilog=__detaildesc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
parser.add_argument('-v', '--verbose', action='count', help='logging verbosity level')
nice_group = parser.add_mutually_exclusive_group(required=False)
nice_group.add_argument('--high', action='store_true', help='Run process as HIGH priority')
nice_group.add_argument('--low', action='store_true', help='Run process as LOW priority')
parser.add_argument('python_script', action='store', help='python script to daemonize')
args = parser.parse_args()


def main():
    pscript = os.path.abspath(args.python_script)
    if args.high:
        subprocess.Popen(['nohup','nice','-n-10','/usr/bin/python3.6',pscript], stdout=subprocess.PIPE)
    elif args.low:
        subprocess.Popen(['nohup','nice','-n10','/usr/bin/python3.6',pscript], stdout=subprocess.PIPE)
    else:
        subprocess.Popen(['nohup', pscript], stdout=subprocess.PIPE)
        #subprocess.Popen(['nohup',pscript,'>/opt/galaxymedia/debug.log','2>&1','&'], stdout=subprocess.PIPE)
    exit(0)


if __name__ == '__main__':
    main()
