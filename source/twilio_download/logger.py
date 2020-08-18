import os
from time import gmtime, strftime

def initialize(): # Adds details about starting run
  pass

def log(message, include_time = True):
  current_path = os.path.dirname(os.path.realpath(__file__))
  logger_loc = os.path.split(current_path)[0] # Path one level up, log location
  if(include_time):
    message = strftime('[%Y %b %d %H:%M:%S] ', gmtime()) + message + '\n'
  with open(logger_loc + '/logger.log', 'a') as f:
    f.write(message)

if __name__ == "__main__":
	log('This is a test')
