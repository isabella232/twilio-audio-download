import sys
import json
import os
import csv
import configparser
from . import RecordingsDecryptor, installpack, logger
import requests

twilio = installpack.checkInstall('twilio')

def getConfigInfo():
  try:
    inifile_name = os.path.dirname(os.path.realpath(__file__)) + '/twilio_settings.ini'
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
    logger.log('Unable to retrieve Twilio credentials: ' + str(e))
    exit() # No point in continuing if unable to retrieve credentials
    # return ['', '', '']

  try:
    privateKeyPath = config['key']['path']
  except:
    key = ''
    # End no path given
  
  if (privateKeyPath != ''):
    try:
      key = RecordingsDecryptor.get_private_key(privateKeyPath)
    except Exception as e:
      logger.log('Error: Unable to process private key:', str(e))
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
    logger.log('There is no file at \'' + csvLocation + '\'. Check the twilio_settings.ini file to make sure the file path is correct under ')
  except Exception as e:
    logger.log('Error while retrieving CSV file info: ' + str(e))
  return values

def main():
  logger.log('Starting audio file retrieval')
  current_loc = os.path.dirname(os.path.realpath(__file__)) # Pathname of this file
  thenrun_loc = os.path.dirname(current_loc) # Pathname of the "thenrun" folder
  data_loc = os.path.dirname(thenrun_loc) # Pathname of the CSV file where the data is being exported to.

  config = getConfigInfo() # Retrieves the info in the twilio_settings.ini file
  if (config == ''):
    logger.log('Config file not found. Exiting.')
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
    logger.log('Unable to retrieve info about the CSV file. Check to make sure each part is present, even if they are blank: ' + str(e))
    exit()

  if data_format == 'wide':
    csv_filename = form_title + '_WIDE.csv' # If the export is wide format
  elif rg_name == '':
    csv_filename = form_title + '.csv' # If the export is long, but not in a repeat group
  else:
    csv_filename = form_title + '-' + rg_name + '.csv' # If the export is wide, and the calling field is in a repeat group

  if (add_group_name == 'True') and (rg_name != None): # Adds the group name to the field name if applicable
    recordingField = rg_name + '-' + recordingField
  
  csvPathname = data_loc + '/' + csv_filename # Full path name of the 
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
        filepath = data_loc + '/Call recordings/'
    except:
      filepath = data_loc + '/Call recordings/'
  except:
    audioFormat = 'wav'
    filepath = data_loc + '/Call recordings/'

  try:
    if not os.path.exists(filepath):
      os.makedirs(filepath)
  except Exception as e:
    logger.log('Error while creating folder: ' + str(e))
  
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
        logger.log('Unable to retrieve recording info: ' + str(e))
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
        RecordingsDecryptor.decrypt_recording(privateKey, fullpath, encryptionDetails['encrypted_cek'], encryptionDetails['iv'])
        # Completed decryption
      
      # end FOR through each recording in the submission
    # end FOR loop through each recording
  logger.log('Completed download')

if __name__ == "__main__":
	main()
