import sys
import subprocess
import ctypes

version_all = sys.version_info
version_num = str(version_all.major) + '.' + str(version_all.minor) + '.' + str(version_all.micro)
message = 'Python version number: '  + version_num
ctypes.windll.user32.MessageBoxW(0, message, 'Python version', 0x0 | 0x40)