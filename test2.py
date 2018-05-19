#!/usr/bin/python3.6

import sys
import json
from modules.galaxymediamod import *

dump = json.dumps(video_info('/mnt/incoming/test3_newnew265.mkv'), sort_keys=True, indent=4)
print('################################################')
print(dump)
