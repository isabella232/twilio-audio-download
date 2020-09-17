#!/usr/bin/python3

import sys
import subprocess
import ctypes

platform = sys.platform

version_all = sys.version_info
version_num = str(version_all.major) + '.' + str(version_all.minor) + '.' + str(version_all.micro)
message = 'Python version number: '  + version_num
title = 'Python version'
if version_all.major < 3:
  message = unicode(message)
  title = unicode(title)

print(message)
try:
  if(platform == 'windows'):
    print('Platform is "windows"')
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x0 | 0x40)
  elif platform == 'darwin':
    print('Platform is "darwin"')
    applescript = 'display dialog "' + message + \
    '" with title "' + title + '" '
    applescript += 'with icon note buttons {"OK"}'

    subprocess.call("osascript -e '{}'".format(applescript), shell=True)
  else:
    print('Platform "' + platform + '" does not support popups.')
except Exception as e:
  print(e)