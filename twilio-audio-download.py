import sys
import json
import os
import csv
import configparser
import installpack
import requests

twilio = installpack.checkInstall('twilio')
from twilio.rest import Client

def getConfigInfo():
  try:
    inifile_name = sys.path[0] + '/twilio_settings.ini'
    config = configparser.ConfigParser()
    config.read(inifile_name)
    return config
  except:
    return ''

def getCredentials(config):
  try:
    credentials = config['twilio']
    sid = credentials['account_sid']
    authtoken = credentials['auth_token']
    privateKey = config['key']['private']
    return [sid, authtoken, privateKey]
  except:
    return ['', '', '']

def getFieldValue(csvLocation, field):
  values = []
  with open(csvLocation, 'r', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      values.append(row[field])
  return values

def main():
  config = getConfigInfo()
  print('starting')
  if (config == ''):
    print('Config file not found. Exiting.')
    exit()

  credentials = getCredentials(config)
  sid, authtoken, key = [credentials[i] for i in range(0, 3)]
  csvFile = config['file']
  csvLocation = csvFile['csv']
  recordingField = csvFile['field']
  recLocs = getFieldValue(csvLocation, recordingField)

  session = requests.Session()
  session.auth = (sid, authtoken)
  client = Client(sid, authtoken)


  try: # Retrieving recording format, and preferred location
    recordingInfo = config['recording']
    try:
      audioFormat = recordingInfo['format']
    except:
      audioFormat = 'wav'
    try:
      filepath = recordingInfo['location']
      if not os.path.exists(filepath):
        os.makedirs(filepath)
    except:
      filepath = ''
  except:
      audioFormat = 'wav'
      filepath = ''

  for r in recLocs:
    response = session.get(r).json()
    recordings = response['recordings']
    for i in recordings:
      apiVersion = i['api_version']
      accountSid = i['account_sid']
      recordingSid = i['sid']
      recordingUrl = 'https://api.twilio.com/' + apiVersion + '/Accounts/' + accountSid + '/Recordings/' + recordingSid

      if audioFormat != 'wav':
        recordingUrl += '.' + audioFormat

      recordingFile = session.get(recordingUrl)
      filename = recordingSid + '.' + audioFormat
      print('File name: ' + filename)
      print('URL: ' + recordingUrl)

      if filepath == '':
        fullpath = filename
      elif filepath.endswith('/') or filepath.endswith('\\'):
        fullpath = filepath + filename

      print('path: ' + fullpath)
      with open(fullpath, 'wb') as f:
        f.write(recordingFile.content)

  


if __name__ == "__main__":
	main()

