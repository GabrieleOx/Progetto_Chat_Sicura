from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


key = get_random_bytes(16)
m="messaggio a16bit"
cipher = AES.new(key, AES.MODE_EAX)
nonce = cipher.nonce


ciphertext, tag = cipher.encrypt_and_digest(m.encode())

decipher=AES.new(key,AES.MODE_EAX,nonce=nonce)
plaintext = decipher.decrypt(ciphertext)
try:

    decipher.verify(tag)
    print("The message has not been corrupted:", plaintext)

except ValueError:

    print("Key incorrect or message corrupted")
