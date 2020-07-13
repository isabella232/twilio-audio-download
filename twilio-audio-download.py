import sys
import json
import os
import csv
import configparser
import installpack


twilio = installpack.checkInstall('twilio')
from twilio.rest import Client

def getConfigInfo():
  try:
    inifile_name = sys.path[0] + '/local.ini'
    config = configparser.ConfigParser()
    config.read(inifile_name)
    return config
  except:
    return ''

def getCredentials(config):
  try:
    credentials = config['credentials']
    username = credentials['username']
    password = credentials['password']
    privateKey = config['key']['private']
    return [username, password, privateKey]
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

  if (config == ''):
    print('Config file not found. Exiting.')
    exit()

  credentials = getCredentials(config)
  username, password, key = [credentials[i] for i in range(0, 3)]
  print(username, password, key)
  csvFile = config['file']
  csvLocation = csvFile['csv']
  recordingField = csvFile['field']
  recLocs = getFieldValue(csvLocation, recordingField)
  print(recLocs)
  twilioCred = config['twilio']
  client = Client(twilioCred['account_sid'], twilioCred['auth_token'])

  # https://www.twilio.com/docs/video/api/recordings-resource#get-media-subresource
  for r in recLocs:
    recording = client.video.recordings(r).fetch()

  


if __name__ == "__main__":
	main()

