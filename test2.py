#!/usr/bin/python3

import modules.loadconfig as cfg

print(cfg.config.getlist('general', 'del_extensions'))
