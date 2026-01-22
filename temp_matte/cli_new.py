import socket
import threading
import time
import os
import hashlib
from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long,long_to_bytes
import pickle as pk
from Crypto.Random import get_random_bytes

public_key=""
private_key= ""
username="MAF3X"
password="ciaooo122"
password2="hallooo275"
sessionKey=0
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
print(long_to_bytes(m).decode())'''

def main():
    HOST = "localhost"
    PORT = 3000
    global sesssionKey
    sessionKey=0
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    stampaChat(sock)
    destinatario=input("inserisci il numero dell'host a cui ti vuoi collegare: ")
    sock.sendall(destinatario.encode())
    thread = threading.Thread(target=listenForMsg, args=("Giovanni", sock)) #inserire il nome del mittente al posto di "Giovanni" #thread per ricevere i messaggi e rimanere in ascolto
    thread.start()
    
    if sessionKey==0:
        #sessionKey=createHashForChat(username, password) #generazione della session key per la chat appena scelta
        sessionKey = get_random_bytes(32)
        to_send_key=cryptWithPublic(sessionKey,"/Users/matteo/Documents/projects/Progetto_Chat_Sicura/temp_matte/public_corrente.der")
        to_send=pk.dumps(("SK", to_send_key))
        sock.sendall(to_send)
        print("session key creata: ", sessionKey)

    end=False
    while not end: 
        msg=input()
        if msg == "end":
            end=True
        elif msg =="cls" or msg == "clear":
            os.system("cls" if os.name == "nt" else "clear")
        else:
            to_send = pk.dumps(("M", msg))
            sock.sendall(to_send)

    sock.close()

def listenForMsg(nomeMittente, sock):
    global sessionKey
    while True:
        try:
            msg = sock.recv(1024)
            recieved = pk.loads(msg)
            if not recieved:
                print("Connessione chiusa.")
                break
            elif recieved[0]=="SK":
                sessionKey=decryptWithPrivate(recieved[1], "/Users/matteo/Documents/projects/Progetto_Chat_Sicura/temp_matte/private_corrente.der")
                print("session key ricevuta: ", sessionKey)
            elif recieved[0]=="M":
                print(nomeMittente + ": " + recieved[1])
        except Exception as e:
            print("Errore in ricezione:", e)
            break

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

    private_key_data = open(path,"rb").read()
    pvt = RSA.import_key(private_key_data, passphrase=password)

    m = pow(c, pvt.d, pvt.n)
    return long_to_bytes(m)

if __name__=="__main__":
    main()

#"/Users/matteo/Documents/projects/Progetto_Chat_Sicura/temp_matte/private_corrente.der"