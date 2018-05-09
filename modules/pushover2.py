#!/usr/bin/python2

import logging
import urllib
import urllib2
from configparser import ConfigParser
import json
import logging

configfile = '/etc/galaxymediatools.cfg'

log = logging.getLogger(__name__)
config = ConfigParser()
config.read(configfile)

def pushover(app_key, title='', msg=''):
    user_key = config.get('pushover', 'user_key')
    config = {
    'api': 'https://api.pushover.net/1/messages.json',
    'user': user_key,
    'token': app_key
    }

    data = urllib.urlencode({
        'user': config['user'],
        'token': config['token'],
        'title': title,
        'message': msg
    })

    try:
        req = urllib2.Request(config['api'], data)

        response = urllib2.urlopen(req)
    except urllib2.HTTPError:
        log.error('Pushover notification failed. HTTPError')
        return False

    res = json.load(response)

    if res['status'] == 1:
        log.info('Pushover notification successfully sent')
    else:
        log.error('Pushover notification failed')
