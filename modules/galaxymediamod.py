#!/usr/bin/python3.6
"""
 fuctions used in galaxymedia scripts

"""

import os
import stat
import subprocess
import logging
import json
from urllib.request import urlopen
from urllib.parse import urlparse
from datetime import datetime
from shutil import copyfile

import ffmpy
import publicsuffix
from pexpect import pxssh
from wakeonlan import send_magic_packet as wol

import modules.loadconfig as cfg
from modules.pushover import Client

log = logging.getLogger()

categories = {'movies': cfg.config.get('plex', 'movie_section'), 'tv': cfg.config.get('plex', 'tv_section'), 'comedy':
cfg.config.get('plex', 'comedy_section'), 'ufc': cfg.config.get('plex', 'ufc_section')}
plextoken = cfg.config.get('plex', 'token')


def video_transcode(in_file, ffmpeg_options):
    log.debug(f'Starting video_transcode function on {in_file}')
    trans_dir = cfg.config.get('directories', 'local_transcode')
    if not is_dirwritable(trans_dir):
        log.error(f'Local transcode directory [{trans_dir}] is not writable. Exiting.')
        exit(1)
    if diskspace(trans_dir)['GBfree'] < 20:
        log.error(f'Local drive transcode dir [{trans_dir}] is under 20 Gig. Exiting.')
        exit(1)
    if not os.path.isfile(in_file):
        log.error(f'Cannot find source video file for transcode {in_file}. Exiting.')
        exit(1)
    if not os.access(in_file, os.W_OK):
        log.error(f'Permissions: Source video file needs to have write access to be replaced. Exiting.')
        exit(1)
    if not os.access(in_file, os.R_OK):
         log.error(f'Permissions: Source video file needs to have read access. Exiting.')
         exit(1)
    log.debug(f'Copying video file to local transcode directory {trans_dir}')
    new_trans_file = f'{trans_dir}/{file_name(in_file)}'
    try:
        copyfile(in_file,new_trans_file)
    except:
        log.error(f'Error copying file {in_file} to local trans dir {trans_dir}')
        exit(1)
    log.debug(f'File copy complete {in_file} > {new_trans_file}')
    post_trans_file = f'{trans_dir}/{file_name_noext(new_trans_file)}.trans.mp4'
    ffmpeg_options = f'-v quiet -stats -loglevel fatal -i "{new_trans_file}" ' + ffmpeg_options + f' "{post_trans_file}"'
    ffmpeg = ffmpy.FFmpeg(global_options=(ffmpeg_options))
    log.debug(f'Starting transcode on video file [{file_name(new_trans_file)}]')
    start_time = datetime.now()
    try:
        ffmpeg.run()
    except:
        log.warning(f'Transcode failed for file {file_name(in_file)}. Adding to failed transcode log.')
        with open(cfg.config.get('logs', 'failed_transcode'), "a") as logfile:
            logfile.write(in_file)
        if os.path.isfile(new_trans_file):
            os.remove(new_trans_file)
        if os.path.isfile(post_trans_file):
            os.remove(post_trans_file)
        return False
    else:
        end_time = datetime.now()
        elapsed = elapsedTime(end_time, start_time)
        log.info(f'Transcode complete.[{int(MB(os.path.getsize(new_trans_file)))}>{int(MB(os.path.getsize(post_trans_file)))}] {elapsed} [{file_name(new_trans_file)}]')
        if os.path.getsize(new_trans_file) + 100000000 < os.path.getsize(post_trans_file):
            log.info('Transcoded file is significantly larger then original. Adding to check transcode log.')
            with open(cfg.config.get('logs', 'check_transcode'), "a") as logfile:
                logfile.write(f'[{int(MB(os.path.getsize(new_trans_file)))} > {int(MB(os.path.getsize(post_trans_file)))})] {in_file}')
            if os.path.isfile(new_trans_file):
                os.remove(new_trans_file)
            if os.path.isfile(post_trans_file):
                os.remove(post_trans_file)
            return False
        log.debug(f'Replacing original video with newly transcoded video [{file_name(new_trans_file)}]')
        try:
            os.remove(in_file)
        except:
            log.error(f'Error removing source video file {in_file}')
            exit(1)
        else:
            try:
                copyfile(post_trans_file, f'{file_dir(in_file)}/{file_name(post_trans_file)}')
            except:
                log.error(f'Error copying file {post_trans_file} > {in_file}')
                exit(1)
            else:
                os.remove(post_trans_file)
                os.remove(new_trans_file)
                log.debug(f'Replaced original video file with transcoded video {file_name(in_file)}')
                return True


def mapvinfo(ffinfo, query):
    try:
        if len(query) == 2:
            return ffinfo[query[0]][query[1]]
        elif len(query) == 3:
            return ffinfo[query[0]][query[1]][query[2]]
    except KeyError:
        return 'N/A'


def video_info(in_file,raw=False):
    info = {}
    ffprobe = ffmpy.FFprobe(global_options=("-loglevel quiet -sexagesimal -of json -show_format -show_streams", f'"{in_file}"'))
    stdout, stderr = ffprobe.run(stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    ff0string = str(stdout, 'utf-8')
    ffinfo = json.loads(ff0string)
    if raw:
        print(json.dumps(ffinfo, sort_keys=True, indent=4))
    info['format'] = mapvinfo(ffinfo, ["format","format_name"])
    info['streams'] = mapvinfo(ffinfo, ["format","nb_streams"])
    info['format_long'] = mapvinfo(ffinfo, ["format","format_long_name"])
    duration = mapvinfo(ffinfo, ["format","duration"]).split('.')
    info['duration'] = duration[0]
    info['bit_rate'] = mapvinfo(ffinfo, ["format","bit_rate"])
    for stream in range(ffinfo["format"]["nb_streams"]):
        info['stream'+str(stream)] = {'codec_type': mapvinfo(ffinfo, ["streams",stream,"codec_type"])}
        if mapvinfo(ffinfo, ["streams",stream,"codec_type"]) != 'data':
            info['stream'+str(stream)].update({'codec_name': mapvinfo(ffinfo, ["streams",stream,"codec_name"])})
        if mapvinfo(ffinfo, ["streams",stream,"codec_type"]) == 'video':
            info['stream'+str(stream)].update({'width': mapvinfo(ffinfo, ["streams",stream,"width"])})
            info['stream'+str(stream)].update({'height': mapvinfo(ffinfo, ["streams",stream,"height"])})
            info['stream'+str(stream)].update({'aspect_ratio': mapvinfo(ffinfo, ["streams",stream,"display_aspect_ratio"])})
            info['stream'+str(stream)].update({'bit_rate': mapvinfo(ffinfo, ["streams",stream,"bit_rate"])})
            #info['stream'+str(stream)].update({'bit_rate': ffinfo["streams"][stream]['tags']["BPS"]})
            info['stream'+str(stream)].update({'level': mapvinfo(ffinfo, ["streams",stream,"level"])})
        elif mapvinfo(ffinfo, ["streams",stream,"codec_type"]) == 'audio':
            info['stream'+str(stream)].update({'channels': mapvinfo(ffinfo, ["streams",stream,"channels"])})
            info['stream'+str(stream)].update({'bit_rate': mapvinfo(ffinfo, ["streams",stream,"bit_rate"])})
    return info


def is_tv_excluded(in_file):
    for edir in cfg.config.getlist('excludes', 'tv_dirs'):
        if dir_is_parent(edir, file_dir(in_file)):
            return True
    return False


def is_dirwritable(dirname):
    user_id = os.geteuid()
    group_id = os.getegid()
    dir_stat = os.stat(dirname)
    directory_mode = dir_stat[stat.ST_MODE]
    if user_id == dir_stat[stat.ST_UID] and stat.S_IRWXU & directory_mode == stat.S_IRWXU:
        return True
    elif group_id == dir_stat[stat.ST_GID] and stat.S_IRWXG & directory_mode == stat.S_IRWXG:
        return True
    elif stat.S_IRWXO & directory_mode == stat.S_IRWXO:
        return True
    else:
        return False


def dir_is_parent(parent_path, child_path):
    parent_path = os.path.abspath(parent_path)
    child_path = os.path.abspath(child_path)
    return os.path.commonpath([parent_path]) == os.path.commonpath([parent_path, child_path])


def video_isinteg(in_file):
    video_extensions = cfg.config.getlist('general', 'video_extensions')
    trans_dir = cfg.config.get('directories', 'local_transcode')
    video_minsize = cfg.config.get('general', 'min_videosize')
    if file_ext(in_file) not in video_extensions:
        log.warning(f'video_isinteg returned bad video extension on file {in_file}')
        return False
    if os.path.getsize(in_file) < int(video_minsize) * 1000000:
        log.warning(f'video_isinteg returned video size too small {int(os.path.getsize(in_file)/1000000)} MB < {video_minsize} MB')
        return False
    log.info(f'Running FFMpeg to check video file {in_file}')
    trans_file = f'{trans_dir}/{file_name(in_file)}'
    check_options = f'-v error -i "{in_file}" -vframes 50 -y -strict -2 "{trans_file}"'
    ffobj = ffmpy.FFmpeg(global_options=(check_options))
    try:
        ffobj.run()
    except ffmpy.FFRuntimeError as e:
        log.warning(f'FFMpeg exitied with error: {e}')
        if os.path.isfile(trans_file):
            log.debug(f'Removing transcode temp file {trans_file}')
            os.remove(trans_file)
        return False
    else:
        if os.path.isfile(trans_file):
            log.debug(f'Removing transcode temp file {trans_file}')
            os.remove(trans_file)
        return True


def MB(in_bytes):
    return float_trunc_1dec(in_bytes / 1000000)

def file_name(in_file):
    in_file_split = in_file.split('/')
    return in_file_split[-1]


def file_name_noext(in_file):
    in_file_split = in_file.split('/')
    filename = in_file_split[-1]
    filename_split = filename.split('.')
    if len(filename_split) == 1:
        log.debug(f'Function file_nameonly returned [{filename_split[0]}] for file {in_file}')
        return filename_split[0]
    filename_split = filename_split[:-1]
    log.debug(f'Function file_nameonly returned [{"".join(filename_split)}] for file {in_file}')
    return ''.join(filename_split)


def file_dir(in_file):
    result = os.path.dirname(in_file)
    if result == "":
        #log.debug(f'Function file_dir returned [.] for file {in_file}')
        return '.'
    else:
        #log.debug(f'Function file_dir returned [{result}] for file {in_file}')
        return result

def file_ext(in_file):
    in_file_split = in_file.split('/')
    filename = in_file_split[-1]
    filename_split = filename.split('.')
    if len(filename_split) == 1:
        log.debug(f'Function file_ext returned *NO* file extension for file {in_file}')
        return ""
    else:
        log.debug(f'Function file_ext returned [{filename_split[-1]}] for file {in_file}')
        return filename_split[-1]

def is_trans(in_file):
    in_file_split = in_file.split('/')
    filename = in_file_split[-1]
    filename_split = filename.split('.')
    for itr in filename_split:
        if itr == 'trans' or itr == 'ntrans':
            log.debug(f'Function is_trans returned TRUE on file {in_file}')
            return True
    log.debug(f'Function is_trans returned FALSE on file {in_file}')
    return False


def is_root():
    user = os.getenv("SUDO_USER")
    if user is None:
        log.debug('Root user check, this *IS NOT* a root user')
        return False
    else:
        log.debug('Root user check, this *IS* a root user')
        return True


def require_root():
    user = os.getenv("SUDO_USER")
    if user is None:
        log.error("This program requires root privledges. Exiting.")
        exit(1)


def remote_cmd(server, username, password, cmd):
    ssh = pxssh.pxssh()
    try:
        ssh.login(server, username, password)
    except pxssh.ExceptionPexpect as e:
        print('Failed to connect to remote server with SSH')
        return False
    else:
        print('SSH connected to remote server [{}]'.format('server'))
        try:
            ssh.sendline(cmd)
            ssh.prompt()
            ssh.sendline('echo $?')
            ssh.prompt()
            splitres = ssh.before.decode().split('\r\n')
            result = splitres[1]
        except:
            print('SSH remote command execution failed')
            return False
        else:
            print('SSH remote command executed successfully')
            return result

def wakeup(macaddr):
    wol(macaddr)


def pushover(app_key, ptitle, message):
    try:
        client = Client(cfg.config.get('pushover', 'user_key'), api_token=app_key)
        client.send_message(message, title=ptitle)
    except Exception as e:
        log.error('Pushover notification failed. Error: %s' % str(e))
        return False
    else:
        log.debug('Pushover notification sent. Title: {}'.format(ptitle))
        return True

def processMedia(category):
    log.info('Executing nzbToMedia for category {}'.format(category))
    ourl = '/mnt/incoming/process/deluge/{}'.format(category)
    log.debug('url to open: {}'.format(ourl))
    try:
        subprocess.call(['/usr/local/nzbToMedia/nzbToMedia.py', ourl, '', category, '', 'generic'])
    except:
        log.exception('Error executing nzbToMedia script for category {}'.format(category))
    else:
        log.info('nzbToMedia executed successfully for category {}'.format(category))

def plex_updatesection(category):
    try:
        urlopen('http://172.25.1.26:32400/library/sections/{}/refresh?X-Plex-Token={}'.format(categories[category],plextoken))
    except:
        log.error('URL Error opening URL for plex section update')
    else:
        log.info('Updates plex section {} successfully'.format(category))

def elapsedHours(stop_time, start_time):
    diff_time = stop_time - start_time
    total_secs = diff_time.seconds
    log.debug('Converted times to elapsed hours [{}] and [{}] to {} Hours'.format(start_time,stop_time,total_secs / 60 / 60))
    return((total_secs/60/60)+(diff_time.days*24))

def elapsedTime(stop_time, start_time,lshort=False):
    log.debug('Converting times to elapsed time [{}] and [{}]'.format(start_time,stop_time))
    diff_time = stop_time - start_time
    days = diff_time.days
    if days == 1:
        daystring = 'Day'
    else:
        daystring = 'Days'
    total_secs = diff_time.seconds
    seconds = total_secs % 60
    if seconds == 1:
        if lshort == False:
            secstring = 'Second'
        else:
            secstring = 'Sec'
    else:
        if lshort == False:
            secstring = 'Seconds'
        else:
            secstring = 'Secs'
    total_min = total_secs / 60
    minutes = int(total_min % 60)
    if minutes == 1:
        if lshort == False:
            minstring = 'Minute'
        else:
            minstring = 'Min'
    else:
        if lshort == False:
            minstring = 'Minutes'
        else:
            minstring = 'Mins'
    hours = int(total_min / 60)
    if hours == 1:
        if lshort == False:
            hourstring = 'Hour'
        else:
            hourstring = 'Hr'
    else:
        if lshort == False:
            hourstring = 'Hours'
        else:
            hourstring = 'Hrs'
    if days != 0:
        log.debug('elapsedTime: {} {}, {} {}, {} {}'.format(days,daystring,hours,hourstring,minutes,minstring))
        return('{} {}, {} {}, {} {}'.format(days,daystring,hours,hourstring,minutes,minstring))
    elif hours != 0:
        log.debug('elapsedTime: {} {}, {} {}'.format(hours,hourstring,minutes,minstring))
        return('{} {}, {} {}'.format(hours,hourstring,minutes,minstring))
    elif minutes != 0:
        log.debug('elapsedTime: {} {}, {} {}'.format(minutes,minstring,seconds,secstring))
        return('{} {}, {} {}'.format(minutes,minstring,seconds,secstring))
    elif minutes == 0:
        log.debug('elapsedTime: {} {}'.format(seconds,secstring))
        return('{} {}'.format(seconds,secstring))
    else:
        log.error('Elapsed time function failed. Could not convert.')
        return('Error')


def float_trunc_1dec(num):
    try:
       tnum = num // 0.1 / 10
    except:
       log.exception('Error truncating float to 1 decimal: {}'.format(num))
       return False
    else:
       return tnum


def float_trunc_2dec(num):
    try:
        tnum = num // 0.01 / 100
    except:
        log.exception('Error truncating float to 1 decimal: {}'.format(num))
        return False
    else:
        return tnum

def trunc_savepath(spath):
    savedir = spath.split('/')
    return savedir[-1]

def trunc_tracker(rawtracker):
    urlres = urlparse(rawtracker)
    urlinfo = (urlres.netloc.split(":"))
    if urlinfo[0] == '':
        return 'NONE'
    else:
        domainret = publicsuffix.PublicSuffixList().get_public_suffix(urlinfo[0])
        log.debug('trunc_tracker returning domain name {} from string {}'.format(domainret,rawtracker))
        return domainret

def datestring2object(datestring):
    if isinstance(datestring, datetime):
       log.debug('datestring is already datetime object, no conversion neded')
       return datestring
    elif isinstance(datestring, str):
       log.debug('datestring {} is string and converting to datetime object'.format(datestring))
       numunixtimea = int(datestring[:-2])
       return datetime.fromtimestamp(numunixtimea)
    elif isinstance(datestring, int):
       log.debug('datestring {} is int and converting to datetime object'.format(datestring))
       return datetime.fromtimestamp(datestring)
    elif isinstance(datestring, float):
       log.debug('datestring {} is float and converting to datetime object'.format(datestring))
       numunixtimea = int(datestring)
       log.debug(numunixtimea)
       return datetime.fromtimestamp(datestring)
    else:
       log.critical('datestring in unknown format, cannot convert')

def diskspace(path):
    if not os.path.exists(path):
        log.error('Invalid path specified for diskspace check: {}'.format(path))
    else:
        if not os.name == 'posix':
            log.error('Diskspace check only supports Linux/Unix environments')
        else:
            try:
                osstatvfs = os.statvfs(path)
                fsbytes = osstatvfs.f_frsize * osstatvfs.f_blocks     # Size of filesystem in bytes
                fsfree = osstatvfs.f_frsize * osstatvfs.f_bavail     # Number of free bytes that ordinary users
                fsmb = fsbytes / 1000000  # convert to MB
                fsmbfree = fsfree / 1000000  # convert to MB
                fskb = fsbytes / 1000
                fskbfree = fsfree / 1000
                fsgb = fsbytes / 1000000000
                fsgbfree = fsfree / 1000000000
            except:
                log.exception('Error while trying to determine disk space for {}'.format(path))
                return False
            else:
                fsreturn = {}
                fsreturn['GBfree'] = round(fsgbfree, 1)
                fsreturn['GBtotal'] = round(fsgb, 1)
                fsreturn['MBfree'] = round(fsmbfree, 1)
                fsreturn['MBtotal'] = round(fsmb, 1)
                fsreturn['KBfree'] = round(fskbfree, 1)
                fsreturn['KBtotal'] = round(fskb, 1)
                fsreturn['Bytesfree'] = round(fsfree, 1)
                fsreturn['Bytestotal'] = round(fsbytes, 1)
                return fsreturn
