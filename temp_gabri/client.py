from colorama import Fore, init #pip install colorama
import os
import pickle as pk #per gestire un dizionario codificato in bytes
from getpass import getpass
import socket as sk
import threading as th

#pip install pycryptodome
from Crypto.PublicKey import RSA #docs RSA: https://pycryptodome.readthedocs.io/en/latest/src/public_key/rsa.html
from Crypto.Hash import SHA256
from Crypto.Util.number import long_to_bytes, bytes_to_long
from Crypto.Cipher import AES #docs per la mode GCM: https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html#gcm-mode

this_private: RSA.RsaKey

def cls(): #funzioncina per pulire lo schermo
    os.system('cls' if os.name == 'nt' else 'clear')

def user_password() -> tuple[str, str]:
    while True:
        username = input("Username: ").strip()
        if len(username) == 0:
            print(Fore.RED + "Username non valido (almeno un carattere)...")
            continue
        else:
            break
    
    password = make_password()
    
    return (username, password)

def make_password() -> str:
    while True:
        ps1h = getpass().strip()
        ps2h = getpass(prompt="Ripeti la password: ").strip()
        if ps1h != ps2h:
            print(Fore.RED + "Le password non coincidono...")
            continue
        elif ps1h == "":
            print(Fore.RED + "La password non può essere vuota...")
            continue
        else:
            break

    return ps1h

def sha256(value: bytes | bytearray) -> bytes:
    hasher = SHA256.new()
    hasher.update(value)
    return hasher.digest()

def login(conn: sk.socket):
    global this_private

    cls()
    print("+---------+")
    print("| Accesso |")
    print("+---------+\n\n")

    #inserimento dati utente:
    username, password = user_password()
    password_hash = sha256(password.encode())

    dati_login = {
        "username" : username,
        "password_hash" : password_hash
    }
    to_send = pk.dumps(("L", dati_login))
    conn.send(to_send)

    #ricevo risposta dal server:
    r = conn.recv(3072)
    ricevuto = pk.loads(r)
    
    if ricevuto[0] == "L":
        data = ricevuto[1]
        match data["code"]:
            case 0:
                this_private = RSA.import_key(data["private_key"], password)
                print(Fore.GREEN + f"Loggato correttamente\ncode: {data["code"]}")
            case 1: print(Fore.RED + f"Login fallito, utente '{username}' insesistente\ncode: {data["code"]}")
            case 2: print(Fore.RED + f"Login fallito, utente '{username}' già loggato\ncode: {data["code"]}")
            case 3: print(Fore.RED + f"Login fallito, password errata\ncode: {data["code"]}")
            case 4: print(Fore.RED + f"Login fallito, errore nel controllo dei dati utente\ncode: {data["code"]}")
            case _: print(Fore.BLUE + "?? Unknown case ??")
    else:
        print(Fore.MAGENTA + "Caso sconosciuto: (possibile manomissione della comunicazione)\nConsigliata la disconnessione...")
    
    input("Premi invio per continuare...")


def signin(conn: sk.socket):
    cls()
    print("+---------------+")
    print("| Registrazione |")
    print("+---------------+\n\n")

    #inserimento dati utente:
    username, password = user_password()

    password_hash = sha256(password.encode())

    nome = input("Nome (opzionale): ").strip()
    cognome = input("Cognome (opzionale): ").strip()

    #generazione chiavi RSA:

    #print(Fore.BLUE + "Cifratura chiave privata:")
    #password_key = make_password()

    new_key = RSA.generate(3072)
    public = new_key.public_key().export_key(format="DER") #DER per averla direttamente in binario
    private = new_key.export_key(format="DER", passphrase=password, pkcs=8) # è possibile renderla ancora più sicura con: protection="PBKDF2WithHMAC-SHA512AndAES256-CBC"

    #popolo il dizionario da inviare
    data_dict = {
        "username" : username,
        "password_hash" : password_hash,
        "public_key" : public,
        "private_key" : private
    }
    if nome != "":
        data_dict["nome"] = nome
    if cognome != "":
        data_dict["cognome"] = cognome
    
    to_send = pk.dumps(("R", data_dict)) # "R" per registrazione e pickle per averli encoded

    conn.send(to_send)
    
    ricevuto = pk.loads(conn.recv(1024))
    if ricevuto[0] == "R":
        match ricevuto[1]:
            case 0: print(Fore.GREEN + f"Registrazione effettuata correttamente\ncode: {ricevuto[1]}")
            case 1: print(Fore.RED + f"Registrazione fallita, utente con username: {username} già presente\ncode: {ricevuto[1]}")
            case 2: print(Fore.RED + f"Registrazione fallita, errore nell'inserimento dei dati\ncode: {ricevuto[1]}")
            case _: print(Fore.BLUE + "??  Unknown case  ??")
    else:
        print(Fore.MAGENTA + "Caso sconosciuto: (possibile manomissione della comunicazione)\nConsigliata la disconnessione...")

    input("Premi invio per continuare...")
    

def start_menu() -> int:
    while True:
        cls()
        print("+-------------------------------+")
        print("| (1) Effettua il login:        |")
        print("| (2) Registra un nuovo utente: |")
        print("| (3) Esci:                     |")
        print("+-------------------------------+")
        
        try:
            selection = int(input(">"))
        except ValueError:
            continue

        if 3 >= selection >= 1:
            break
    return selection

def main():
    init(autoreset=True) #solo per il colore del testo

    address = ("localhost", 6789) #address = (host, port)
    conn = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    try:
        conn.connect(address)
    except:
        print(Fore.RED + f"Connessione a server remoto {address} fallita.")
        exit(0)

    #connessione riuscita:

    while True:
        selection = start_menu() # 1: Login | 2: Registrazione | 3: Uscita
        if selection == 3:
            conn.close()
            print(Fore.RED + "Arrivederci...")
            exit(0)
        
        match selection:
            case 1: login(conn)
            case 2: signin(conn)
            case _: break
    
    conn.close() #chiusura "forzata" da un errore o altro

if __name__ == "__main__":
    main()