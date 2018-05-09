#!/usr/bin/python3

import logging
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
from configparser import ConfigParser

configfile = '/etc/galaxymediatools.cfg'
config = ConfigParser()
config.read(configfile)
log = logging.getLogger()

pURL = 'http://{}:32400/status/sessions?X-Plex-Token={}'.format(config.get('servers', 'plex_ip'),config.get('plex', 'token'))

def isplex_alive():
    try:
        urlopen(pURL).read()
    except:
        log.warning('Plex server status returned DOWN')
        return False
    else:
        log.debug('Plex server status returned UP')
        return True


def isplex_idle():
    try:
        sauce = urlopen(pURL).read()
    except:
        log.error('URL Error quering plex server for status')
    else:
        log.debug('Plex server status update successfully')
        soup = bs(sauce,'xml')

        inputTag = soup.find("MediaContainer")
        output = int(inputTag['size'])
        if output > 0:
            log.info('Plex server status returned NOT IDLE')
            return False
        else:
            log.info('Plex server status returned IDLE')
            return True


print(isplex_idle())

