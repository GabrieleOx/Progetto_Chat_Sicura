import socket
import threading
import time
import os
import hashlib
from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long,long_to_bytes
import pickle as pk
from Crypto.Random import get_random_bytes

import json
from base64 import b64encode
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64decode

def main():
    key=b'\x14I\x89{\xa8!&\xdf\xeb\x15\xe5v(3\xfe\xe4\xdfgk\xc9\xcf\x85\xbd\xb6\xb4/`\x0eH\x94\x19-'

    plainText=input("inserisci un testo: ")

    msg=simmetriCryption(plainText, key)
    print("------------> ",msg)
    deciphered=simmetricDecryption(msg, key)
    print("------------> ",deciphered)

def simmetriCryption(plainText, key):
    header = b"header"
    data = plainText.encode()
    cipher = AES.new(key, AES.MODE_GCM)
    cipher.update(header)
    ciphertext, tag = cipher.encrypt_and_digest(data)

    json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
    json_v = [ b64encode(x).decode('utf-8') for x in (cipher.nonce, header, ciphertext, tag) ]
    result = json.dumps(dict(zip(json_k, json_v)))
    return result

def simmetricDecryption(cipherText, key):
    try:
        b64 = json.loads(cipherText)
        json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
        jv = {k:b64decode(b64[k]) for k in json_k}
        cipher = AES.new(key, AES.MODE_GCM, nonce=jv['nonce'])
        cipher.update(jv['header'])
        plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
        return plaintext.decode('utf-8')
    except (ValueError, KeyError):
        return "Incorrect decryption"
    
if __name__=="__main__":
    main()