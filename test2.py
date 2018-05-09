#!/usr/bin/python3

import git 

g = git.cmd.Git('/opt/galaxymedia')
try:
    g.pull()
except:
    print('Failed.')
else:
    print('Success.')
