import hashlib
import time
import pickle as pk

timestamp=0

def sha256_hash(plainText):
    hash_object = hashlib.sha256(plainText.encode())
    digest = hash_object.digest()
    return digest

def createHashForChat(usr, password):
    global timestamp
    timestamp=int(time.time())
    to_hash=str(sha256_hash(usr))+str(sha256_hash(password))+str(timestamp)
    return sha256_hash(to_hash)

username="" #120 Bytes
password="" #32 Bytes
print("len time: ",len(pk.dumps(timestamp)))
sessionKey=createHashForChat(username, password) # unica funzione da richiamare per fare screare la session key
print("len session key: ",len(sessionKey))