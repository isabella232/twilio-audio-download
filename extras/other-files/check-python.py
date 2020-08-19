import sys
import subprocess

# INSTALLATION FUNCTIONS

def install(package):
  print('Installing ' + package)
  subprocess.check_call([sys.executable, "-m", "pip", "install", package])
  print('Installation of ' + package + ' was successful')

def checkInstall(moduleName, packageName=None): # Returns the module
  try:
    module = importlib.import_module(moduleName, package=packageName)
  except:
    try:
      install(moduleName)
      module = importlib.import_module(moduleName, package=packageName)
    except Exception as e:
      print('Sorry, but the installation failed:', e)
      exit()
    # End module not installed
  return module
# End checkInstall

# END INSTALLATION FUNCTIONS

checkInstall('ctypes')
import ctypes

version_all = sys.version_info
version_num = str(version_all.major) + '.' + str(version_all.minor) + '.' + str(version_all.micro)
message = bytes('Python version number: '  + version_num, 'utf-8')
ctypes.windll.user32.MessageBoxW(0, message, u'Python version', 0x0 | 0x40)