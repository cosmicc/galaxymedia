#!/usr/bin/python3.6

import sys
import json
from modules.galaxymediamod import *

dump = json.dumps(video_info('/mnt/storage/video/TV Series/Gold Rush/Season 08/Gold Rush - S08E01 - Wagers and Wars.mkv'), sort_keys=True, indent=4)
print('################################################')
print(dump)
