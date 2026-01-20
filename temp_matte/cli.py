import socket
import threading
import time
import os
import hashlib

public_key=""
private_key= ""
username="MAF3X"
password="ciaooo122"

def main():
    HOST = "localhost"
    PORT = 3000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    stampaChat(sock)
    destinatario=input("inserisci il numero dell'host a cui ti vuoi collegare: ")
    sock.sendall(destinatario.encode())
    sessionKey=createHashForChat(username, password) #generazione della session key per la chat appena scelta
    thread = threading.Thread(target=listenForMsg, args=("Giovanni", sock)) #inserire il nome del mittente al posto di "Giovanni"
    thread.start()

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

def listenForMsg(nomeMittente, sock): #thread che rivece e rimane in ascolto di messaggi
    while True:
        msg = sock.recv(1024).decode()
        print(nomeMittente+": "+msg)

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

if __name__=="__main__":
    main()