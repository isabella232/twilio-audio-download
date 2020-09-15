#!/usr/bin/python3

import sys
import os
import csv
from time import gmtime, strftime
import subprocess
import importlib
import codecs
import ctypes
import re
import glob


platform = sys.platform
folder_separator = ('/' if platform.startswith('darwin') or platform.startswith('linux') else '\\')

current_path = os.path.realpath(__file__)
file_folder = os.path.dirname(current_path)
working_folder = os.path.dirname(file_folder) + folder_separator # This is the folder with the CSV file, the log file, and most of the other files we'll be working with
os.chdir(working_folder)

error_popup = False

def popup(title, message):
  try:
    if platform == 'windows':
      ctypes.windll.user32.MessageBoxW(0, message, title, 0x0 | 0x40)
    elif platform == 'darwin':
      applescript = 'display dialog "' + message + \
      '" with title "' + title + '" '
      applescript += 'with icon note buttons {"OK"}'

      subprocess.call("osascript -e '{}'".format(applescript), shell=True)
  except Exception as e:
    log('Error while creating popup:' + str(e))

# Logging function for error checking
def log(message, show_popup = False, include_time = True):
  if include_time:
    message = strftime('[%Y %b %d %H:%M:%S] ', gmtime()) + message + '\n'
  print(message)
  with open(working_folder + 'recording.log', 'a') as f:
    f.write(message)
  
  if show_popup == True:
    error_popup = True # For showing popup at the end if there is an error that warrants one.

# INSTALLATION FUNCTIONS

def install(package):
  log('Installing ' + package)
  subprocess.check_call([sys.executable, "-m", "pip", "install", package, '--user'])
  log('Installation of ' + package + ' was successful')

def checkInstall(moduleName, packageName=None):
  try:
    module = importlib.import_module(moduleName, package=packageName)
  except:
    try:
      install(moduleName)
    except Exception as e:
      log('Sorry, but the installation failed: ' + str(e), True)
      exit()
    
    # End module not installed
# End checkInstall

# END INSTALLATION FUNCTIONS

checkInstall('configparser')
checkInstall('requests')
checkInstall('cryptography')

import configparser
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

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
    config = configparser.ConfigParser()
    home_path = str(os.path.expanduser('~'))

    config_path = home_path + folder_separator + 'twilio_settings.ini'
    if(os.path.exists(config_path)):
      config.read(config_path)
    elif os.path.exists('twilio_settings.ini'):
      config.read('twilio_settings.ini') # If not in the home path, then check the working directory
    else:
      log('Unable to find twilio_settings.ini file in either home directory or export folder.', True)
      exit()

    return config
  except Exception as e:
    log('Error while retrieving twilio_settings.ini file: ' + str(e))

# Retrieves the account sid, auth token, and private key. For the private key, it takes the file, and processes it into a way that can be used by the decryptor. That way, the key does not have to be reprocessed each time.
def getCredentials(config):
  try:
    credentials = config['twilio']
    sid = credentials['account_sid']
    authtoken = credentials['auth_token']
  except Exception as e:
    log('Unable to retrieve Twilio credentials: ' + str(e), True)
    exit() # No point in continuing if unable to retrieve credentials
    # return ['', '', '']

  try:
    privateKeyPath = config['key']['path']
  except:
    key = ''
    # End no path given
  
  if privateKeyPath != '':
    try:
      key = get_private_key(privateKeyPath)
    except Exception as e:
      log('Error: Unable to process private key:', str(e), True)
      key = ''
  else: # If no path to private key is defined
    key = ''
    # End check for private key
  # End found a path for the key
  return [sid, authtoken, key]

def getFieldValue(csvLocations, fieldname): # Returns URIs to the recordings so they can be retrieved
  fieldname_len = len(fieldname)
  values = {} # This will eventually store each URI to access each recording. In this dictionary, name of the property will be the file name, to make sure file names are not repeated

  for csv_file in csvLocations:
    with open(csv_file, 'r') as f:
      reader = csv.reader(f)
      all_headers = next(reader) # Retrieves the columns headers
    
    if 'PARENT_KEY' in all_headers:
      long_format = True
    else:
      long_format = False

    uri_headers = []
    for header in all_headers:
      regex = re.search(fieldname, header, re.IGNORECASE) # Search for the field name, ignoring case
      if regex != None:
        uri_headers.append([header, regex.end(0)]) # Adds header to the list of URI headers if it contains the field name, default 'twilio_call_recordings_url'. Also adds when it ends, which is used later.

    with open(csv_file, 'r', newline='') as opened_csv:
      reader = csv.DictReader(opened_csv)

      for row in reader:
        full_uuid = row['KEY']
        uuid_simp = full_uuid[5:41]
        if long_format: # If is is in long format, then the file name can contain group name and instance information
          try:
            row_group_name = re.search('(?<=\/)[^\[]+', full_uuid).group(0) # Group name of for the row
            repeat_instance = re.search('(?<=\[)[^\]]+', full_uuid).group(0) # Repeat instance number
            filename_prefix = uuid_simp + '-' + row_group_name + '_' + repeat_instance
          except Exception as e:
            log('Issue getting KEY info, may not have all downloaded all recordings: ' + str(e))
            filename_prefix = uuid_simp
        else:# If is is in wide format, then the file name can only contain instance information
          filename_prefix = uuid_simp

        for u in uri_headers:
          uri_header = u[0]
          end_pos = u[1]
          header_suffix = uri_header[end_pos:] # Suffix starts when the text that was searched for (default 'twilio_call_recordings_url') ends. For example, if header is called 'this_twilio_call_recordings_url_123', then the value of header_suffix will be '_123'.
          field_value = row[uri_header]
          if re.fullmatch('https:\/\/api\.twilio\.com\/2010-04-01\/Accounts\/AC[a-z\d]+\/Calls\/CA[a-z\d]+\/Recordings.json', field_value) == None: # If not in correct format, then move on to the next value
            continue
          
          recording_filename = filename_prefix + header_suffix
          
          field_num = 0
          name_ending = '' # This will be (1), (2), so on. Starts blank, since if there are no name doubles, then no need to add this
          while field_num < 20: # This is for checking if the file name is already being used
            try:
              values[recording_filename + name_ending] # Hopefully, this fails, meaning the file name does not exist. If it does now fail, add to var "field_num", and try with that
            except:
              if field_num != 0:
                recording_filename += name_ending # If the file name created is already being used, adds a number to differentiate it
              values[recording_filename] = field_value
              break
            field_num += 1
            name_ending = ' (' + str(field_num) + ')'
            # End while through numbers
          if field_num == 20:
            log('There were too many fields that contain "' + fieldname + '" in their name, so not all recordings have been downloaded.', True)
          # Done checking the header
        # Done checking the row
      # Done opening the file
    # Done with the file name

  if len(values) == 0:
    log('No recordings found in CSV file')
    exit()
  return values

def main():
  log('Starting audio file retrieval')

  if not sys.version_info.major == 3:
    log('Error: You are not using Python 3 to run this script.', True)
    exit()

  config = getConfigInfo() # Retrieves the info in the twilio_settings.ini file
  if config == '':
    log('twilio_settings.ini file not found. Exiting.', True)
    exit()

  credentials = getCredentials(config) # Retrieve Twilio credentials and private key
  sid, authtoken, privateKey = [credentials[i] for i in range(0, 3)]

  all_csv_files = glob.glob("*.csv") # Retrieve a list of all CSV files in the folder.

  try:
    recording_fieldname = config['file']['field_name']
  except:
    recording_fieldname = 'twilio_call_recordings_url'

  recLocs = getFieldValue(all_csv_files, recording_fieldname) # Returns a list of all call recordings

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
        filepath = working_folder + folder_separator + 'Call recordings' + folder_separator
    except:
      filepath = working_folder + folder_separator + 'Call recordings' + folder_separator
  except:
    audioFormat = 'wav'
    filepath = working_folder + folder_separator + 'Call recordings' + folder_separator

  try:
    if not os.path.exists(filepath):
      os.makedirs(filepath)
  except Exception as e:
    log('Error while creating folder: ' + str(e), True)
    new_filepath = working_folder + folder_separator + 'Call recordings' + folder_separator
    if filepath == new_filepath: # If it is the default folder name that cannot be created, then there is no alternative folder name, so exiting
      log('Try specifying an existing folder instead. Exiting...')
      exit()
    else:
      filepath = new_filepath # Since specified folder cannot be created, will use the default path name instead
      try:
        if not os.path.exists(filepath):
          os.makedirs(filepath)
      except Exception as e:
        log('Unable to create alternative folder: ' + str(e), True)
        log('Exiting...')
        exit()
  
  for base_filename in recLocs:
    recording_uri = recLocs[base_filename]

    try:
      raw_response = session.get(recording_uri)
      response = raw_response.json()
    except Exception as e:
      log('Unable to retrieve recording: ' + str(e), True)
      continue

    recordings = response['recordings']
    recording_number = 0
    num_recordings = len(recordings)
    for i in recordings: # In the json, 'recordings' is a list, so this iterates through each one. There will usually only be one iteration.
      if num_recordings > 1:
        recording_number += 1
        filename = base_filename + '_' + str(num_recordings)
      else:
        filename = base_filename
      try:
        recordingSid = i['sid'] # Id of the recording
        encryptionDetails = i['encryption_details'] # Encryption details, if applicable

        # Creating the name of the file
        if encryptionDetails == None:
          filename = filename + '.' + audioFormat # Name is based on the unique identifier of the form or repeat instance. If there are multiple recordings for that field for some reason, it numbers them starting at the second one
        else:
          filename = filename + '.wav.enc'

        if not (filepath.endswith('/') or filepath.endswith('\\')): # Adds ending slash or backslash if needed
          filepath += folder_separator
        
        fullpath = filepath + filename # Exactly where the file will be saved to

        # This is so it does not download files it already has
        if encryptionDetails == None:
          if os.path.exists(fullpath):
            continue
        else:
          decrypted_filename = filename + '-decrypted.wav'
          decrypted_fullpath = filepath + decrypted_filename
          if os.path.exists(decrypted_fullpath):
            continue

        # These parts are used to create the URI that can retrieve the recording file that have not already been retrieved
        apiVersion = i['api_version']
        accountSid = i['account_sid']
        recordingUrl = 'https://api.twilio.com/' + apiVersion + '/Accounts/' + accountSid + '/Recordings/' + recordingSid

      except Exception as e:
        log('Unable to retrieve recording info: ' + str(e), True)
        continue

      if (encryptionDetails == None) and (audioFormat != 'wav'):
        recordingUrl += '.' + audioFormat

      if encryptionDetails != None: # Currently, can only download encrypted recordings in .wav format
        audioFormat = 'wav'
      
      recordingFile = session.get(recordingUrl) # Uses the created URI to retrieve the actual recording

      with open(fullpath, 'wb') as f:
        f.write(recordingFile.content) # Actual putting of the file into the folder

      if encryptionDetails != None : # Decryption, if applicable
        decrypt_recording(privateKey, fullpath, encryptionDetails['encrypted_cek'], encryptionDetails['iv'])
        # Completed decryption
      
      # end FOR through each recording in the submission
    # end FOR loop through each recording
  log('Completed download')
  if error_popup:
    popup('Error', 'There was an issue while downloading the call recordings. Please see the recording.log file for details.')

# END MAIN TWILIO FUNCTIONS

if __name__ == "__main__":
	main()
