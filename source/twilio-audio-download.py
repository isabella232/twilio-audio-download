#!/usr/bin/python

import sys
import json
import os
import csv
from time import gmtime, strftime
import subprocess
import importlib
import codecs

# Logging function for error checking
def log(message, include_time = True):
  current_path = os.path.dirname(os.path.realpath(__file__))
  logger_loc = os.path.dirname(current_path) # Path one level up, log location
  if(include_time):
    message = strftime('[%Y %b %d %H:%M:%S] ', gmtime()) + message + '\n'
  print(message)
  with open(logger_loc + '/recording_log.log', 'a') as f:
    f.write(message)

# INSTALLATION FUNCTIONS

def install(package):
  log('Installing ' + package)
  subprocess.check_call([sys.executable, "-m", "pip", "install", package])
  log('Installation of ' + package + ' was successful')

def checkInstall(moduleName, packageName=None): # Returns the module
  try:
    module = importlib.import_module(moduleName, package=packageName)
  except:
    try:
      install(moduleName)
      module = importlib.import_module(moduleName, package=packageName)
    except:
      log('Sorry, but the installation failed:', sys.exc_info()[0])
      exit()
    
    # End module not installed
  return module
# End checkInstall

# END INSTALLATION FUNCTIONS

checkInstall('configparser')
checkInstall('requests')
checkInstall('cryptography')
checkInstall('ctypes')

import configparser
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import ctypes

# DECRYPTION

# Creates the pathname to be used for the decrypted file
def decrypt_path(enc_path):
	dotLocation = enc_path.rfind('.wav.enc')
	beforeDot = enc_path[0:dotLocation]
	# pathExtension = enc_path[dotLocation:]
	decryptedPath = beforeDot + '-decrypted.wav'
	return decryptedPath

def get_private_key(path):
	private_key = open(path, mode="r")
	key = serialization.load_pem_private_key(private_key.read().encode(), password=None, backend=default_backend())
	private_key.close()
	return key

def decrypt_recording(key, encrypted_path, encrypted_cek, iv):
	# This code sample assumes you have added cryptography.hazmat library to your project

	# Follow "Per Recording Decryption Steps"
	# https://www.twilio.com/docs/voice/tutorials/call-recording-encryption#per-recording-decryption-steps-customer

	# 1) Obtain encrypted_cek, iv parameters within EncryptionDetails via recordingStatusCallback or
	# by performing a GET on the recording resource

	# 2) Retrieve customer private key corresponding to public_key_sid and use it to decrypt base 64 decoded
	# encrypted_cek via RSAES-OAEP-SHA256-MGF1

	decrypted_recording_file_path = decrypt_path(encrypted_path)

	# Python2 version:
#	 decrypted_cek = key.decrypt(
#		 encrypted_cek.decode('base64'),
#		 padding.OAEP(
#			 mgf=padding.MGF1(algorithm=hashes.SHA256()),
#			 algorithm=hashes.SHA256(),
#			 label=None
#		 )
#	 )

	# Python3 version:
	decrypted_cek = key.decrypt(
		codecs.decode(encrypted_cek.encode(), 'base64'),
		padding.OAEP(
			mgf=padding.MGF1(algorithm=hashes.SHA256()),
			algorithm=hashes.SHA256(),
			label=None
		)
	)
 
	# 3) Initialize a AES256-GCM SecretKey object with decrypted CEK and base 64 decoded iv

	# Python2 version:
#	 decryptor = Cipher(
#		 algorithms.AES(decrypted_cek),
#		 modes.GCM(iv.decode('base64')),
#		 backend=default_backend()
#	 ).decryptor()

	# Python3 version:
	decryptor = Cipher(
		algorithms.AES(decrypted_cek),
		modes.GCM(codecs.decode(iv.encode(), 'base64')),
		backend=default_backend()
	).decryptor()

	# 4) Decrypt encrypted recording using the SecretKey

	decrypted_recording_file = open(decrypted_recording_file_path, "wb")
	encrypted_recording_file = open(encrypted_path, "rb")

	for chunk in iter(lambda: encrypted_recording_file.read(4 * 1024), b''):
		decrypted_chunk = decryptor.update(chunk)
		decrypted_recording_file.write(decrypted_chunk)

	decrypted_recording_file.close()
	encrypted_recording_file.close()

# END DECRYPTION

# MAIN TWILIO FUNCTIONS

def getConfigInfo():
  try:
    inifile_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + '/twilio_settings.ini'
    config = configparser.ConfigParser()
    config.read(inifile_name)
    return config
  except:
    return ''

# Retrieves the account sid, auth token, and private key. For the private key, it takes the file, and processes it into a way that can be used by the decryptor. That way, the key does not have to be reprocessed each time.
def getCredentials(config):
  try:
    credentials = config['twilio']
    sid = credentials['account_sid']
    authtoken = credentials['auth_token']
  except Exception as e:
    log('Unable to retrieve Twilio credentials: ' + str(e))
    exit() # No point in continuing if unable to retrieve credentials
    # return ['', '', '']

  try:
    privateKeyPath = config['key']['path']
  except:
    key = ''
    # End no path given
  
  if (privateKeyPath != ''):
    try:
      key = get_private_key(privateKeyPath)
    except Exception as e:
      log('Error: Unable to process private key:', str(e))
      key = ''
  else: # If no path to private key is defined
    key = ''
    # End check for private key
  # End found a path for the key
  return [sid, authtoken, key]

def getFieldValue(csvLocation, field, data_format): # Returns URIs to the recordings so they can be retrieved
  values = [] # This will eventually store each URI to access each recording
  try:
    with open(csvLocation, 'r', newline='') as csvfile:
      reader = csv.DictReader(csvfile) # Opening the SurveyCTO export CSV file as a dictionary reader

      if data_format == 'wide': # If it is in wide format, then checks each possible field header in numeric order. For example, if the field used for Twilio calls is called "twilio_call", then it will first check for the header "twilio_call_1", then "twilio_call_2", and so on. This will end prematurely if one is missing. For example, if "twilio_call_3" does not exist, then it will not bother to check for "twilio_call_4". It also does not work with nested repeats. In those cases, long format should be used.
        for row in reader:
          repeat_num = 0
          while True:
            repeat_num += 1
            header_name = field + '_' + str(repeat_num)
            try:
              field_value = row[header_name]
              if field_value == '':
                break
              values.append(field_value)
            except:
              break
            # end WHILE
          # end FOR
        # end processing data in WIDE format
      else: # Not wide, so must be long format
        for row in reader:
          values.append(row[field])
  except FileNotFoundError:
    log('There is no file at \'' + csvLocation + '\'. Check the twilio_settings.ini file to make sure the form name and group name are correct.')
  except Exception as e:
    log('Error while retrieving CSV file info: ' + str(e))
  return values

def main():
  log('Starting audio file retrieval')

  if not sys.version_info.major == 3:
    log('Python 3 not installed.')
    ctypes.windll.user32.MessageBoxW(0, u'Error: The script was not run with Python 3. Make sure the script is set to be run with Python 3. If Python 3 is not installed, go to the Windows Store to install Python 3, then run this script again. You can install it at https://microsoft.com/p/python-38/9mssztt1n39l.', u'Python 3 error', 0x0 | 0x30)
    exit()

  current_loc = os.path.dirname(os.path.realpath(__file__)) # Pathname of this file
  thenrun_loc = os.path.dirname(current_loc) # Pathname of the "thenrun" folder
  # data_loc = os.path.dirname(thenrun_loc) # Pathname of the CSV file where the data is being exported to.

  config = getConfigInfo() # Retrieves the info in the twilio_settings.ini file
  if (config == ''):
    log('Config file not found. Exiting.')
    exit()

  credentials = getCredentials(config) # Retrieve Twilio credentials and private key
  sid, authtoken, privateKey = [credentials[i] for i in range(0, 3)]

  try:
    csvFileInfo = config['file'] # Retrieves info about the CSV data export
    form_title = csvFileInfo['form_title'] # Form title, which is used in the CSV file name
    rg_name = csvFileInfo['rg_name'] # Repeat group name
    data_format = csvFileInfo['format'] # Whether the data is in long or wide format. Will assume long if not specified
    add_group_name = csvFileInfo['add_group_name']
    recordingField = csvFileInfo['field']
  except Exception as e:
    log('Unable to retrieve info about the CSV file. Check to make sure each part is present, even if they are blank: ' + str(e))
    exit()

  if data_format == 'wide':
    csv_filename = form_title + '_WIDE.csv' # If the export is wide format
  elif rg_name == '':
    csv_filename = form_title + '.csv' # If the export is long, but not in a repeat group
  else:
    csv_filename = form_title + '-' + rg_name + '.csv' # If the export is wide, and the calling field is in a repeat group

  if (add_group_name == 'True') and (rg_name != None): # Adds the group name to the field name if applicable
    recordingField = rg_name + '-' + recordingField
  
  csvPathname = thenrun_loc + '/' + csv_filename # Full path name of the 
  recLocs = getFieldValue(csvPathname, recordingField, data_format) # Returns a list of all call recordings

  session = requests.Session() # Starting HTTP session
  session.auth = (sid, authtoken)

  try: # Retrieving recording format, and preferred location
    recordingInfo = config['recording']
    try:
      audioFormat = recordingInfo['format']
    except:
      audioFormat = 'wav'
    try:
      filepath = recordingInfo['location']
      if filepath == '' or filepath == None:
        filepath = thenrun_loc + '/Call recordings/'
    except:
      filepath = thenrun_loc + '/Call recordings/'
  except:
    audioFormat = 'wav'
    filepath = thenrun_loc + '/Call recordings/'

  try:
    if not os.path.exists(filepath):
      os.makedirs(filepath)
  except Exception as e:
    log('Error while creating folder: ' + str(e))
  
  for r in recLocs:
    response = session.get(r).json() # Uses the values "r" stored using getFieldValue() as URIs in the GET command
    recordings = response['recordings']
    for i in recordings: # In the json, 'recordings' is a list, so this iterates through each one. There will usually only be one iteration.
      try:
        encryptionDetails = i['encryption_details'] # Encryption details, if applicable

        # These parts are used to create the URI that can retrieve the recording file
        apiVersion = i['api_version']
        accountSid = i['account_sid']
        recordingSid = i['sid']
        recordingUrl = 'https://api.twilio.com/' + apiVersion + '/Accounts/' + accountSid + '/Recordings/' + recordingSid

        # To be added: Use the "recordingSid" to check if the file has already been downloaded, and if so, moves on the the next iteration with "continue" command
      except Exception as e:
        log('Unable to retrieve recording info: ' + str(e))
        continue

      if (encryptionDetails == None) and (audioFormat != 'wav'):
        recordingUrl += '.' + audioFormat

      if (encryptionDetails != None): # Currently, can only download encrypted recordings in .wav format
        audioFormat = 'wav'
      
      recordingFile = session.get(recordingUrl) # Uses the created URI to retrieve the actual recording

      # Creating the name of the file
      if encryptionDetails == None:
        filename = recordingSid + '.' + audioFormat
      else:
        filename = recordingSid + '.' + audioFormat + '.enc'

      # Uses the name of the file to create the filepath where the file will be placed
      if filepath == '':
        fullpath = filename
      elif filepath.endswith('/') or filepath.endswith('\\'):
        fullpath = filepath + filename

      with open(fullpath, 'wb') as f:
        f.write(recordingFile.content) # Actual putting of the file into the folder

      if(encryptionDetails != None): # Decryption, if applicable
        decrypt_recording(privateKey, fullpath, encryptionDetails['encrypted_cek'], encryptionDetails['iv'])
        # Completed decryption
      
      # end FOR through each recording in the submission
    # end FOR loop through each recording
  log('Completed download')

# END MAIN TWILIO FUNCTIONS

if __name__ == "__main__":
	main()
