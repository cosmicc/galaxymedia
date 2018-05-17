#!/usr/bin/python3.6

import sys
import subprocess
import json

import ffmpy

ffprobe = ffmpy.FFprobe(global_options=("-loglevel quiet -sexagesimal -of json -show_format -show_streams", sys.argv[1]))

print("ffprobe.cmd:", ffprobe.cmd)  # printout the resulting ffprobe shell command

stdout, stderr = ffprobe.run(stderr=subprocess.PIPE, stdout=subprocess.PIPE)

# std* is byte sequence, but json in Python 3.5.2 requires str
ff0string = str(stdout, 'utf-8')

ffinfo = json.loads(ff0string)
print(json.dumps(ffinfo, indent=4))  # pretty print

#print("Video Dimensions: {}x{}".format(ffinfo["streams"][0]["width"], ffinfo["streams"][0]["height"]))
#print("Streams Duration:", ffinfo["streams"][0]["duration"])
print("Format Name: ", ffinfo["format"]["format_name"])
print("Streams: ", ffinfo["format"]["nb_streams"])
for stream in range(ffinfo["format"]["nb_streams"]):
    print(f'Codec Type: {ffinfo["streams"][stream]["codec_type"]}', end='')
    print(f' Name: {ffinfo["streams"][stream]["codec_name"]}', end='')
    if ffinfo["streams"][stream]["codec_type"] == 'video':
        print(f' Size: {ffinfo["streams"][stream]["width"]}', end='')
        print(f'x{ffinfo["streams"][stream]["height"]}')
    if ffinfo["streams"][stream]["codec_type"] == 'audio':
        print(f' Channels: {ffinfo["streams"][stream]["channels"]}', end='')
#        print(f' Language: {ffinfo["streams"][stream]["tags"]["language"]}', end='')
    print('\n')

