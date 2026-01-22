import socket
import threading
import time
import os
import hashlib
import pickle as pk
from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long,long_to_bytes
from Crypto.Random import get_random_bytes

#stop_event = threading.Event()

sessionKey=0

public_key=""
private_key= ""
username="MAF3X"
password="ciaooo122"
password2="hallooo275"

'''
public_key_data=open("/Users/matteo/Documents/projects/Progetto_Chat_Sicura/temp_matte/public_corrente.der","rb").read()
pub=RSA.import_key(public_key_data)
#print(f"e={pub.e} n={pub.n}")

private_key_data=open("/Users/matteo/Documents/projects/Progetto_Chat_Sicura/temp_matte/private_corrente.der","rb").read()
pvt=RSA.import_key(private_key_data,passphrase=password)
#print(f"d={pvt.d}\nn={pvt.n}")



t="ciao sono un messaggiooooo. Che bello essere un messaggio"
messaggio_trasformato_in_intero=bytes_to_long(t.encode())
n=pub.n
e=pub.e
encrypted=pow(messaggio_trasformato_in_intero,e,n) #cripto con la pubblica
d=pvt.d
m=pow(encrypted,d,n)#decrypto con la privata
print(long_to_bytes(m).decode())

'''
def main():
    HOST = "localhost"
    PORT = 3000
    global sessionKey

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    #ascolto = threading.Thread(target=listenForSK, args=(sock,)) #rimane in asdcolto in caso qualcuno voglia mandargli la session key
    #ascolto.start()

    stampaChat(sock)
    destinatario=input("inserisci il numero dell'host a cui ti vuoi collegare: ")
    sock.sendall(destinatario.encode())
    #sessionKey=createHashForChat(username, password) #generazione della session key per la chat appena scelta
    
    thread = threading.Thread(target=listenForMsg, args=("Giovanni", sock)) #inserire il nome del mittente al posto di "Giovanni"
    thread.start()
    #stop_event.set()
    if sessionKey==0:
        sessionKey = get_random_bytes(32) # AES-256
        print("chiave: ",sessionKey)
        encrypted_sk = cryptWithPublic(sessionKey, "/Users/matteo/Documents/projects/Progetto_Chat_Sicura/temp_matte/public_altro.der")
        sock.sendall(encrypted_sk)
    #ascolto.join()
    #thread.start()

    end=False
    while not end: 
        msg=input().encode()
        if msg.decode() == "end":
            end=True
        elif msg.decode() =="cls" or msg.decode() == "clear":
            os.system("cls" if os.name == "nt" else "clear")
        else:
            sock.sendall(msg)

    sock.close()

def listenForMsg(nomeMittente, sock):
    global sessionKey
    if sessionKey==0:
        msg = sock.recv(1024)
        sessionKey = decryptWithPrivate(msg,"/Users/matteo/Documents/projects/Progetto_Chat_Sicura/temp_matte/private_altro.der")
        print("chiave ricevuta -> ",sessionKey)

    while True:
        try:
            msg = sock.recv(1024)
            if not msg:
                print("Connessione chiusa.")
                break
            print(nomeMittente + ": " + msg.decode())
        except Exception as e:
            print("Errore in ricezione:", e)
            break

def listenForSK(sock):
    global sessionKey
    while not stop_event.is_set():
        msg = sock.recv(4096) #3072
        sessionKey = decryptWithPrivate(msg)

def stampaChat(sock): #stampa i nomi di tutti i destinatari connessi al srv
    msg=""
    msg=sock.recv(1024)
    print(msg.decode())

def sha256_hash(plainText):
    hash_object = hashlib.sha256(plainText.encode())
    digest = hash_object.hexdigest()
    return digest

def createHashForChat(usr, password):
    timestamp=int(time.time())
    to_hash=str(sha256_hash(usr))+str(sha256_hash(password))+str(timestamp)
    return sha256_hash(to_hash)

def cryptWithPublic(data: bytes, path: str):
    public_key_data = open(path,"rb").read()
    pub = RSA.import_key(public_key_data)

    m = bytes_to_long(data)
    c = pow(m, pub.e, pub.n)
    return long_to_bytes(c)

def decryptWithPrivate(cipherText: bytes, path: str):
    c = bytes_to_long(cipherText)

    private_key_data = open("/Users/matteo/Documents/projects/Progetto_Chat_Sicura/temp_matte/private_corrente.der","rb").read()
    pvt = RSA.import_key(private_key_data, passphrase=password)

    m = pow(c, pvt.d, pvt.n)
    return long_to_bytes(m)

if __name__=="__main__":
    main()