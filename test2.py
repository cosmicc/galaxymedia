#!/usr/bin/python3.6

import sys
from modules.galaxymediamod import *

info = video_info(sys.argv[1])
print(info)
print(info['stream0']['codec_type'])

