#!/usr/bin/python3
"""
 media directories cleanup tool

"""

import os
import sys
import logging
import argparse
from pathlib import Path

import modules.processlock as processlock
import modules.loadconfig as cfg

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"
__progname__ = "dircleaner"


BAD_EXTENSIONS = cfg.config.getlist('general', 'del_extensions')
pdirs = ['/mnt/incoming/process/movies', '/mnt/incoming/process/tv', '/mnt/incoming/process/comedy', '/mnt/incoming/process/concerts', '/mnt/incoming/process/ufc', '/mnt/storage/video/Movies', '/mnt/storage/video/TV Series', '/mnt/storage/video/UFC Events', '/mnt/storage/video/Comedy']

log = logging.getLogger()
parser = argparse.ArgumentParser(prog=__progname__)
parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))
parser.add_argument('-q', '--quiet', action='store_true', help='supress logging output to console. default: error logging')
parser.add_argument('-v', '--verbose', action='store_true', help='verbose output (warning)')
parser.add_argument('-vv', '--info', action='store_true', help='more verbose output (info)')
parser.add_argument('-vvv', '--debug', action='store_true', help='full verbose output (debug)')
parser.add_argument('-l', '--logfile', help='log output to a specified file. default: no log to file')
parser.add_argument('-s', '--filesize', default=30, help='file size in meg considered too small to keep. default: 30')
args = parser.parse_args()
if args.debug == True:
    log.setLevel(logging.DEBUG)
elif args.info == True:
    log.setLevel(logging.INFO)
elif args.verbose == True:
    log.setLevel(logging.WARNING)
else:
    log.setLevel(logging.ERROR)
console_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
log_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
if args.quiet is False:
    log_console = logging.StreamHandler()
    log.addHandler(log_console)
    log_console.setFormatter(console_format)
if args.logfile is not None:
    log_fileh = logging.FileHandler(args.logfile)
    log.addHandler(log_fileh)
    log_fileh.setFormatter(log_format)

errordet = 0
filesdel = 0
dirsdel = 0
tremdirs = 0
linksdel = 0

def main():
    processlock.lock()
    if os.path.ismount('/mnt/incoming'):
        log.debug('/mnt/incoming is mounted. continuing.')
    else:
        log.critical('/mnt/incoming is NOT mounted. Exiting.')
        exit()
    for pdir in pdirs:
        log.info('processing directory [{}]'.format(pdir))
        for root, dirs, files in os.walk(pdir, topdown=False):
            for name in files:
                cleanFile(os.path.join(root, name))
        removeEmptyFolders(pdir)
    endIt()

def float_trunc_1dec(num):
    try:
        tnum = num // 0.1 / 10
    except:
        log.exception('Error truncating float to 1 decimal: {}'.format(num))
        return False
    else:
        return tnum

def endIt():
    if errordet != 0:
        log.error('directory processing completed with errors. {} errors, {} dirs deleted, {} files deleted, {} links unlinked, {} dirs remain'.format(errordet,dirsdel,filesdel,linksdel,tremdirs))
    elif dirsdel != 0 or filesdel != 0 or linksdel != 0:
        log.warning('directory processing completed. {} errors, {} dirs deleted, {} files deleted, {} links unlinked, {} dirs remain'.format(errordet,dirsdel,filesdel,linksdel,tremdirs))
    else:
        log.info('directory processing completed. {} errors, {} dirs deleted, {} files deleted, {} links unlinked, {} dirs remain'.format(errordet,dirsdel,filesdel,linksdel,tremdirs))
    if errordet != 0 and not args.quiet:
        print('SCRIPT COMPLETED WITH ERRORS!')
    elif errordet == 0 and not args.quiet:
        print('Script completed successfully.')
    if not args.quiet:
        print('{} errors, {} directories deleted, {} links unlinked, {} files deleted'.format(errordet,dirsdel,linksdel,filesdel))
        print('{} directories remain with files'.format(tremdirs))

def remove_file(rfile):
    global errordet
    global filesdel
    try:
        os.remove(rfile)
    except OSError:
        log.error('error deleting file [{}]',format(rfile))
        errordet += 1
    else:
        log.debug('file deleted successfully [{}]'.format(rfile))
        filesdel += 1

def cleanFile(cfile):
    global linksdel
    log.debug('Processing file [{}]'.format(cfile))
    if os.path.islink(cfile):
        log.debug('symbolic link detected. unlinking link [{}]'.format(cfile))
        try:
            os.unlink(cfile)
        except:
            log.error('error trying to unlink symbolic link [{}]'.format(cfile))
            errordet += 1
            return
        else:
            log.debug('symbolic link successfully unlinked [{}]'.format(cfile))
            linkdel += 1
            return
    cfilext = Path(cfile).suffix
    log.debug('[{}] extension found in [{}]'.format(cfilext,cfile))
    if cfilext in BAD_EXTENSIONS:
        log.info('bad extension found, removing file [{}]'.format(cfile))
        remove_file(cfile)
        return
    fsize = float_trunc_1dec(os.path.getsize(cfile) / 100000)
    log.debug('[{} Meg] file size found in file [{}]'.format(fsize,cfile))
    if fsize < args.filesize:
        log.debug('[{} Meg] is too small to keep for file {}'.format(fsize,cfile))
        remove_file(cfile)

    
def remove_empty_dir(path):
    global errordet
    global dirsdel
    try:
        os.rmdir(path)
    except OSError:
        log.error('error removing directory [{}]'.format(path))
        errordet += 1
    else:
        log.debug('empty directory removed successfully [{}]'.format(path))
        dirsdel += 1

def removeEmptyFolders(path):
    global tremdirs
    log.debug('looking for empty folders on path [{}]'.format(path))
    for root, dirnames, filenames in os.walk(path, topdown=False):
        for dirname in dirnames:
            realdir = os.path.realpath(os.path.join(root, dirname))
            numitems = len(os.listdir(realdir))
            log.debug('[{}] items found in dir [{}]'.format(numitems, realdir))
            if numitems == 0:
                log.debug('empty directory found [{}]'.format(realdir))
                remove_empty_dir(realdir)
            else:
                log.debug('directory not empty and will remain [{}]'.format(realdir))
                tremdirs += 1

if __name__ == '__main__':
        main()
