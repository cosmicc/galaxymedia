#!/usr/bin/python3

import sys
import subprocess
import json

import ffmpy

ffprobe = ffmpy.FFprobe(global_options=("-loglevel quiet -sexagesimal -of json -show_entries stream=width,"
"height,duration -show_entries format=duration -select_streams v:0", sys.argv[1]))

print("ffprobe.cmd:", ffprobe.cmd)  # printout the resulting ffprobe shell command

stdout, stderr = ffprobe.run(stderr=subprocess.PIPE, stdout=subprocess.PIPE)

# std* is byte sequence, but json in Python 3.5.2 requires str
ff0string = str(stdout, 'utf-8')

ffinfo = json.loads(ff0string)
print(json.dumps(ffinfo, indent=4))  # pretty print

print("Video Dimensions: {}x{}".format(ffinfo["streams"][0]["width"], ffinfo["streams"][0]["height"]))
print("Streams Duration:", ffinfo["streams"][0]["duration"])
print("Format Duration: ", ffinfo["format"]["duration"])
