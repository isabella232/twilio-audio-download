#!/usr/local/bin/python3

from . import installpack, logger

installpack.checkInstall('cryptography')

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# For Python 3 only:
import codecs

def decrypt_path(enc_path):
	dotLocation = enc_path.rfind('.')
	beforeDot = enc_path[0:dotLocation]
	pathExtension = enc_path[dotLocation:]
	decryptedPath = beforeDot + '-decrypted' + pathExtension
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


if __name__ == "__main__":
	decrypt_recording()
