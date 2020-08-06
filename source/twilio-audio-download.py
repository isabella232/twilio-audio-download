import sys
import json
import os
import csv
import configparser
import installpack
import requests
import decryptor

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
  except:
    return ['', '', '']

  try:
    privateKeyPath = config['key']['path']
  except:
    key = ''
    # End no path given
  
  if (privateKeyPath != None) and (privateKeyPath != ''):
    try:
      # ('Private key path:', privateKeyPath)
      key = decryptor.loadKeyFile(privateKeyPath)
    except Exception as e:
      print('Unable to load decryptor:', e)
      key = ''
  else: # If no path to private key is defined
    key = ''
    # End check for private key
  # End found a path for the key
  return [sid, authtoken, key]

def getFieldValue(csvLocation, field):
  values = []
  with open(csvLocation, 'r', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      values.append(row[field])
  return values

def decryptAudio(encDetails, privateKey):
  encType = encDetails['type']
  publicKeySid = encDetails['public_key_sid']
  encCek = encDetails['encrypted_cek']
  encIv = encDetails['iv']
  return [encType, publicKeySid, encCek, encIv]

def main():
  config = getConfigInfo()
  print('starting')
  if (config == ''):
    print('Config file not found. Exiting.')
    exit()

  credentials = getCredentials(config)
  sid, authtoken, privateKey = [credentials[i] for i in range(0, 3)]
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

      if filepath == '':
        fullpath = filename
      elif filepath.endswith('/') or filepath.endswith('\\'):
        fullpath = filepath + filename

      with open(fullpath, 'wb') as f:
        f.write(recordingFile.content)

      encryptionDetails = i['encryption_details']
      print(encryptionDetails)
      if(encryptionDetails != None):
        decryptor.decrypt(privateKey, encryptionDetails['encrypted_cek'], encryptionDetails['iv'], fullpath)
        # Completed decryption
      
      # end FOR through each recording in the submission
    # end FOR loop through each recording




if __name__ == "__main__":
	main()

