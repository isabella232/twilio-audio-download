# Based on https://github.com/TwilioDevEd/encrypted-media-recordings/blob/master/voice-recordings-decryptor/python/RecordingsDecryptor.py

# Help from # https://www.twilio.com/docs/voice/tutorials/voice-recording-encryption

import installpack
import sys

installpack.checkInstall('cryptography')

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def loadKeyFile(privateKeyPath):
  try:
    keyFile = open(privateKeyPath, mode='r')
  except Exception as e:
    print('Key not found at specified location:', e)
    return ''

  try:
    keyData = keyFile.read()
    byteKey = bytes(keyData, 'utf-8')
    key = serialization.load_pem_private_key(byteKey, password=None, backend=default_backend())
    print('Key info retrieved')
  except Exception as e:
    print('Error:', e)

  keyFile.close()
  print('From loadKeyFile: ', key)
  return key

def decrypt(key, encryptedCek, iv, encryptedPath):
  if key == '':
    print('No valid key. Cannot decrypt.')
    return

  print('type:', type(key))
  # if(type(key) is str):
  #   key = bytes(key, 'utf-8')

  # if(type(encryptedCek) is str):
  #   encryptedCek = bytes(encryptedCek, 'utf-8')

  print('From decrypt: ', key)
  print('encryptedCek:', encryptedCek)
  dotLocation = encryptedPath.rfind('.')
  beforeDot = encryptedPath[0:dotLocation]
  pathExtension = encryptedPath[dotLocation:]
  decryptedPath = beforeDot + '-decrypted' + pathExtension
  decryptedCek = key.decrypt(
    encryptedCek.decode('base64'),
    padding.OAEP(
      mgf=padding.MGF1(algorithm=hashes.SHA256()),
      algorithm=hashes.SHA256(),
      label=None
    )
  )

  decryptor = Cipher(
    algorithms.AES(decrypted_cek),
    modes.GCM(iv.decode('base64')),
    backend=default_backend()
  ).decryptor()

  decryptedFile = open(decryptedFile, 'wb')
  encryptedFile = open(encryptedPath, 'rb')

  for chunk in iter(lambda: encryptedFile.read(4 * 1024), ''):
    decrypted_chunk = decryptor.update(chunk)
    decryptedFile.write(decrypted_chunk)
  
  decryptedFile.close()
  encryptedFile.close()
  print('Completed decryption')



def test():
  loadKeyFile('/Users/max.s.haberman/Documents/Encryption keys/My First Key_PRIVATEDONOTSHARE.pem')

if __name__ == "__main__":
	test()
