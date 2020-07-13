import subprocess
import importlib
import sys

def install(package):
  print('Installing ' + package + ', please wait...')
  subprocess.check_call([sys.executable, "-m", "pip", "install", package])
  print('Installation of ' + package + ' is complete.')

def checkInstall(moduleName, packageName=None): # Returns the module
  try:
    module = importlib.import_module(moduleName, package=packageName)
  except:
    try:
      install(moduleName)
      module = importlib.import_module(moduleName, package=packageName)
    except:
      print('Sorry, but the installation failed:', sys.exc_info()[0])
      exit()
    
  # End module not installed
  return module
# End checkInstall

def main():
  moduleName = input('Module name: ')
  install(moduleName)

if __name__ == "__main__":
	main()