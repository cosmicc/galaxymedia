#!/usr/bin/python3
"""
 program description

 other usless information
"""

import os
import shutil
import sys
import logging
from configparser import ConfigParser

from modules.galaxymediamod import *

__author__ = "Ian Perry"
__copyright__ = "Copyright 2018, Galaxy Media"
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Ian Perry"
__email__ = "ianperry99@gmail.com"
__progname__ = "nzbToMedia_custom"

configfile = '/etc/galaxymediatools.cfg'
config = ConfigParser()
config.read(configfile)
log = logging.getLogger()
log.setLevel(logging.INFO)
log_format = logging.Formatter('%(asctime)s:[%(levelname)s]:%(name)s:%(message)s')
log_console = logging.StreamHandler()
log.addHandler(log_console)
log_console.setFormatter(log_format)
log_fileh = logging.FileHandler('/mnt/incoming/logs/nzbToMedia_custom.log')
log.addHandler(log_fileh)
log_fileh.setFormatter(log_format)

COMEDY_DIR = config.get('directories', 'comedy_dir')
FILES_DIR = config.get('directories', 'files_dir')
UFC_DIR = config.get('directories', 'ufc_dir')
GAMES_DIR = config.get('directories', 'games_dir')
app_key = config.get('pushover', 'deluge_key')

def sanitizeFilename(filename):
    fnsplit = filename.split('.')
    extension = fnsplit[-1]
    fnsplit = fnsplit[:-1]
    newfile = ' '.join(fnsplit)
    newfile = newfile.replace("_", " ")
    filereturn = [newfile,extension,'{}.{}'.format(newfile,extension)]
    return filereturn

def recursive_permissions(cdir):
    try:
        for root, dirs, files in os.walk(cdir):
            os.chmod(root, 0o0777)
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o0777)
            for f in files:
                os.chmod(os.path.join(root, f), 0o0777)
    except:
        log.exception('Error setting permissions for {}'.format(cdir))
    else:
        log.debug('Successfully set permissions for {}'.format(cdir))

def recursive_overwrite(src, dest, ignore=None):
    if os.path.isdir(src):
        if not os.path.isdir(dest):
            os.makedirs(dest)
        files = os.listdir(src)
        for f in files:
                recursive_overwrite(os.path.join(src, f),
                                    os.path.join(dest, f),
                                    ignore)
    else:
        shutil.copyfile(src, dest)

def checkDir(cdir):
    if not os.path.isdir(cdir):
        log.debug('Destination directory does not exist, creating it.')
        try:
            os.mkdir(cdir, 0o0777)
        except:
            log.exception('Error creating destination directory')
            exit(1)

def processFiledir(source, dest):
    log.debug('Determining if source is file or directory')
    if os.path.isdir(source):
         log.debug('source is a directory, deleting directory tree')
         try:
             recursive_overwrite(source, dest)
         except:
             log.exception('Error copying directory to destination {}'.format(dest))
             exit(1)
         else:
             log.debug('Directory copied successfully {}'.format(source))
             recursive_permissions(dest)
             try:
                 shutil.rmtree(source)
             except:
                 log.exception('Error removing source directory {}'.format(source))
                 exit(1)
             else:
                 log.debug('Source directory removed successfully {}'.format(source))
                 exit(0)
    else:
         log.debug('source is a file, copying file to destination {}'.format(dest))
         ddest = '{}(1)'.format(dest)
         if os.path.isfile(ddest):
             try:
                 os.remove(ddest)
             except:
                 log.exception('Error removing file {}'.format(ddest))
                 exit(1)
             else:
                 log.debug('Successfully Removed File: {}'.format(ddest))
         if os.path.isfile(dest):             
             try:
                 shutil.move(dest, ddest)
             except:
                 log.exception('Error renaming file {}'.format(dest))
                 exit(1)
             else:
                 log.debug('Successfully Removed File: {}'.format(dest))
         try:
             shutil.copy(source, dest)
         except:
             log.exception('Error copying file to destination {}'.format(dest))
             exit(1)
         else:
             log.debug('File copied successfully, removing source')
             try:
                 os.remove(source)
             except:
                 log.exception('Error removing source file {}'.format(source))
                 exit(1)
             else:
                 log.debug('Source file removed successfully {}'.format(source))
                 return True

try:
    category = sys.argv[1]
    mediarootdir = sys.argv[2]
    mediafilefull = sys.argv[3]
    mediafilenodir = sys.argv[4]
    log.debug('arg1: {} arg2: {} arg3: {} arg4: {}'.format(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]))
except:
    log.critical('Not enough arguments given.')
    log.error('1: {}'.format(sys.argv[1]))
    log.error('2: {}'.format(sys.argv[2]))
    log.error('3: {}'.format(sys.argv[3]))
    log.error('4: {}'.format(sys.argv[4]))

try:
    mfolder = mediarootdir.split('/')
    mediafolder = mfolder[-1]
except:
    log.critical('Error detemining media folder without path')

if category == "files":
    if os.path.isdir(mediarootdir):
       log.info('Processing dir: {} for category: {}'.format(mediarootdir,category))
       if processFiledir(mediarootdir, '{}{}'.format(FILES_DIR,mediafolder)):
            retfile = sanitizeFilename(mediafilenodir)
            pushoverSend(app_key,'Download Finished', retfile[0])
elif category == "games":
    if os.path.isdir(mediarootdir):
       log.info('Processing dir: {} for category: {}'.format(mediarootdir,category))
       if processFiledir(mediarootdir, '{}{}'.format(GAMES_DIR,mediafolder)):
           retfile = sanitizeFilename(mediafilenodir)
           pushoverSend(app_key,'Download Finished', retfile[0])
elif category == "comedy":
    log.info('Processing file: {} for category: {}'.format(mediafilenodir,category))
    if processFiledir(mediafilefull, COMEDY_DIR):
       plex_updatesection(category)
       retfile = sanitizeFilename(mediafilenodir)
       pushoverSend(app_key,'Download Finished', retfile[0])
       log.info('Processing file {} completed successfully'.format(mediafilenodir))
elif category == "ufc":
    log.info('Processing file: {} for category: {}'.format(mediafilenodir,category))
    if processFiledir(mediafilefull, UFC_DIR):
       plex_updatesection(category)
       retfile = sanitizeFilename(mediafilenodir)
       pushoverSend(app_key,'Download Finished', retfile[0])
       log.info('Processing file {} completed successfully'.format(mediafilenodir))
#elif category == "music":
#    if os.path.isdir(mediarootdir):
#       log.info('Processing dir: {} for category: {}'.format(mediarootdir,category))
#       if processFiledir(mediarootdir, '{}{}'.format(MUSIC_DIR,mediafolder)):
#           retfile = sanitizeFilename(mediafilenodir)
#           pushoverSend(app_key,'Download Finished', retfile[0])

