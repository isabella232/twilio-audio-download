import sys
import subprocess
import ctypes

version_all = sys.version_info
version_num = str(version_all.major) + '.' + str(version_all.minor) + '.' + str(version_all.micro)
message = 'Python version number: '  + version_num
title = 'Python version'
if version_all.major < 3:
  message = unicode(message)
  title = unicode(title)

print(message)

try:
  ctypes.windll.user32.MessageBoxW(0, message, title, 0x0 | 0x40)