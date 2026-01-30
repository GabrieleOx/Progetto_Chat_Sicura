#installare librerie per tutto:
import subprocess
import sys
from pathlib import Path

req = Path(__file__).parent / "requirements.txt"

subprocess.check_call([
    sys.executable,
    "-m",
    "pip",
    "install",
    "-r",
    str(req)
])

from colorama import Fore, init #pip install colorama 
import pickle as pk
import socket as sk
import mariadb as db #pip install mariadb
import threading as th
import time as tm
import struct as st
from random_word import RandomWords

init(autoreset=True)
ADDRESS = ("localhost", 3000)

random_words = RandomWords()
client_loggati: dict[str, sk.socket] = {} # username : connessione al client
chats = {}     # chat_id -> (id1, id2, ...)
lock = th.Lock()

db_params = { #credenziali database utenti
    "user" : "progetto_chat",
    "password" : "password-server",
    "host" : "localhost",
    "database" : "progetto_chat_sicura"
}


def sendall(socket: sk.socket, data: bytes):
    """
    Funzione per l'invio di dati dopo la dimensione di essi
    
    :param socket: socket su cui inviare
    :type socket: sk.socket
    :param data: dati da inviare
    :type data: bytes
    """

    lenght = st.pack("!I", len(data))
    socket.sendall(lenght)
    socket.sendall(data)

def recvall(sock: sk.socket, n: int) -> bytes | None:
    """
    Funzione per ricevere tutti i dati entro un range di bytes
    
    :param sock: socket da cui ricevere
    :type sock: sk.socket
    :param n: range di bytes da ricevere
    :type n: int
    :return: dati ricevuto oppure None
    :rtype: bytes | None
    """

    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def recv(conn: sk.socket) -> bytes | None:
    """
    Funzione per ricevere messaggi interi
    
    :param conn: socket da cui ricevere
    :type conn: sk.socket
    :return: Dati ricevuti o None
    :rtype: bytes | None
    """

    raw_len = recvall(conn, 4)
    if raw_len is not None:
        msg_len = st.unpack('!I', raw_len)[0]

    data = recvall(conn, msg_len)
    return data

def start_chat(utenti_chiavi: dict[str, bytes | bool]):
    global chats

    """
    Avvio della chat inviando la SK al destinatario
    
    :param a: ID del primo client
    :param b: ID del secondo client
    :param sessionKey: chiave di sessione simmetrica
    """

    with lock:
        if any(not (str(user) in client_loggati.keys()) for user in utenti_chiavi.keys()):
            return

        #generazione nome della chat e controllo che non esista già con quel nome
        chat_id = str(random_words.get_random_word())
        while chat_id in chats.keys():
            chat_id = str(random_words.get_random_word())

        try:
            chats[chat_id] = [str(user) for user in utenti_chiavi.keys()]

            #invio della SK e conferma a chi l'ha creata
            for usr, key in utenti_chiavi.items():
                sendall(client_loggati[usr], pk.dumps(("O", [chat_id, tuple(str(user) for user in utenti_chiavi.keys() if str(user) != usr), key]))) # True e False stanno per: hai startato tu?
        except:
            #in caso di errori cancello la chat: oppure non dovrei??????
            if chat_id in chats.keys():
                chats.pop(chat_id)


def relay(chat_id, sender, text, sender_color):
    """
    Reindirizza il messaggio al canale insieme a chi lo manda

    :param chat_id: id della chat
    :param sender: id di chi manda il messaggio
    :param text: messaggio
    """

    with lock:

        #controlloc che la chat esista
        if chat_id not in chats:
            return
        
        people = chats[chat_id] #people in chat
        targets = tuple(user for user in people if user != sender)
        
        for target in targets:
            if target in client_loggati:
                sendall(client_loggati[target], pk.dumps(("M", [chat_id, sender, text, sender_color])))

def add_users(data: dict): #dizionario con chat_id e utenti da aggiungere e chiavi

    chat_id = data["chat"]
    new_people: list[str] = [str(u) for u in data["keys"].keys()]
    keys: dict[str, bytes] = data["keys"] #dizionario con nuovo utente -> chiave crittata

    if chat_id not in chats.keys():
        return
    
    people_before: list[str] = [u for u in chats[chat_id]]
    
    lenght_before = len(chats[chat_id])
    
    for user in new_people:
        if user in client_loggati.keys():
            if user not in chats[chat_id]: #aggiungo gli utenti che non sono già dentro e sono loggati
                chats[chat_id].append(user)
    
    if lenght_before < len(chats[chat_id]):
        for user in chats[chat_id]:
            if user in client_loggati.keys():
                if user in people_before:
                    #per l'update mando solo chat_id e utenti -> tutti, compresi quelli vecchi
                    sendall(client_loggati[user], pk.dumps(("A", [chat_id, tuple(u for u in chats[chat_id] if u != user)]))) #A per Add users to chat
                else:
                    sendall(client_loggati[user], pk.dumps(("O", [chat_id, tuple(u for u in chats[chat_id] if u != user), keys[user]])))



def close_chat(chat_id):
    """
    Chiude la chat con l'ID specificato
    
    :param chat_id: ID del canale chat
    """

    with lock:
        if chat_id not in chats:
            return
        
        people = chats.pop(chat_id)

        # chiude da tutti i lati, se non si sono già disconessi
        for user in people:
            if user in client_loggati:
                sendall(client_loggati[user], pk.dumps(("C", chat_id)))

def registration(data: dict) -> int:
    """
    Insert dei dati sul DB con controllo dell'uscita...
    
    :param data: dati da inserire nel db
    :type data: dict
    :return: 0: tutto ok, 1: errore utente già presente, 2: errore nell'insermento dei dati
    :rtype: int
    """

    utente = {str(key) : data[str(key)] for key in data.keys() if str(key) not in ["pbkey", "pvkey"]}
    chiavi = {str(key) : data[str(key)] for key in data.keys() if str(key) in ["pvkey", "pbkey", "username"]}

    username = data["username"]

    with db.connect(**db_params) as conn:
        with conn.cursor() as cur:

            try:
                #controllo che l'utente non esista già
                cur.execute("SELECT username FROM utente")
                utenti = [row[0] for row in cur.fetchall()]
                if username in utenti:
                    return 1
                
                #inserisco i dati
                cur.execute(f"INSERT INTO utente ({",".join(str(key) for key in utente.keys())}) VALUES ({",".join("?" for i in range(len(utente)))})", tuple(utente[key] for key in utente.keys()))

                #inserisco le chiavi
                cur.execute(f"INSERT INTO user_key ({",".join(str(key) for key in chiavi.keys())}) VALUES ({",".join("?" for i in range(len(chiavi)))})", tuple(chiavi[key] for key in chiavi.keys()))
                conn.commit()
            except:
                #cancello tutto in caso di errore
                cur.execute("DELETE FROM utente WHERE username = ?", (username,))
                conn.commit()
                return 2
    
    return 0

def access(data: dict, conn_client: sk.socket):
    """
    Verifica i dati ricevuti per l'accesso con quelli presenti sul DB
    
    :param data: dati da verificare col db
    :type data: dict
    :return: 0: loggato correttamente, 1: errore utente inesistente, 2: errore utente già loggato, 3: errore password errata
    :rtype: int
    """
    global client_loggati
    username = data["username"]
    password_hash = data["password_hash"]

    with db.connect(**db_params) as conn:
        with conn.cursor() as cur:

            try:
                #controllo che l'utente esista
                cur.execute("SELECT username, password, colore FROM utente")
                utenti_pass = {row[0] : (row[1], row[2]) for row in cur.fetchall()} #tupla password colore

                if username not in utenti_pass.keys():
                    return (1,)
                
                # e non sia già loggato
                if username in client_loggati.keys():
                    return (2,)
                
                #verifica della password
                if password_hash == utenti_pass[username][0]:
                    client_loggati[username] = conn_client
                    cur.execute("SELECT k.pvkey FROM user_key k JOIN utente u ON u.username = k.username WHERE u.username = ?", (username,))
                    conn.commit()
                    pvkey: bytes = cur.fetchone()[0]
                    return (0,(utenti_pass[username][1], pvkey))
                else: return (3,)
            except:
                return (4,)
    return (4,)



def request_key(usernames: list[str]) -> tuple[int] | tuple[int, dict[str, bytes]]:
    """
    Richiesta della chiave pubblica di una lista di utenti
    
    :param usernames: gli username di cui si chiede la PbK
    :type username: list[str]
    :return: singolo codice di errore | codice di uscita e PbK
    :rtype: tuple[int] | tuple[int, dict[str, bytes]]
    """

    with db.connect(**db_params) as conn:
        with conn.cursor() as cur:

            try:
                #controllo che gli utenti esistano
                cur.execute("SELECT username FROM utente")
                users = [str(row[0]) for row in cur.fetchall()]
                pb_keys: dict[str, bytes] = {}
                
                for username in usernames:
                    #controllo che esista
                    if username not in users:
                        return (1,)
                    
                    #controllo che sia online
                    if username not in client_loggati.keys():
                        return (2,)

                    cur.execute("SELECT pbkey FROM user_key WHERE username = ?", (username,))
                    conn.commit()
                    
                    pbkey: bytes = cur.fetchone()[0]
                    pb_keys[username] = pbkey

                return (0, pb_keys)
            except:
                return (3,)
    
    return (3,)


def loggato(username: str, conn: sk.socket):
    """
    Ricettore dei messaggi del client loggato
    
    :param username: username dell'utente che si è loggato
    :type username: str
    :param conn: socket corrispondente al client
    :type conn: sk.socket
    """

    while True:
        data = recv(conn)
        if not data:
            break
            
        recived = pk.loads(data)
        match recived[0]:
            case "E":
                username_remove = recived[1]
                client_loggati.pop(username_remove)
                break #esce dall "modalità loggato"

            case "K":
                ex = request_key(recived[1])
                #controllo se sto aggiungendo utenti o creando chat nuova:
                if len(recived) != 4:
                    sendall(conn, pk.dumps(("K", ex)))
                else:
                    d = {"keys" : ex, "chat_id" : recived[3]}
                    sendall(conn, pk.dumps(("AK", d))) #ritorno chiavi pubbliche e chat_id

            case "S": start_chat(recived[1])

            case "M": relay(recived[1][0], username, recived[1][1], recived[1][2])

            case "C": close_chat(recived[1])

            case "A": add_users(recived[1]) #dizionario con chat_id e utenti da aggiungere e chiavi


def handle(conn: sk.socket, addr):
    """
    Funzione di gestione del nuovo client connesso
    
    :param conn: socket del client connesso
    :type conn: sk.socket
    :param addr: indirizzo del client connesso
    """

    print(Fore.GREEN + f"Connesso {addr}")

    while True:
        try:
            recived = recv(conn) #valore alto per tranquillità
            if not recived:
                break

            recived = pk.loads(recived)

            match recived[0]: #smista le richieste
                case "R": 
                    code = registration(recived[1])
                    sendall(conn, pk.dumps(("R", code)))
                case "L":
                    ex = access(recived[1], conn)            
                    data_dict: dict[str, int | bytes] = {
                        "code" : ex[0]
                    }
                    if ex[0] == 0:
                        client_loggati[recived[1]["username"]] = conn
                    if len(ex) == 2:
                        data_dict["private_key"] = ex[1][1]
                        data_dict["colore"] = ex[1][0]
                    sendall(conn, pk.dumps(("L", data_dict)))
                    if ex[0] == 0:
                        loggato(recived[1]["username"], conn)
        except:
            break
    
    conn.close() # Disconnessione sicura

    #sicurezza per chiusura processi \/ (caso Ctrl + C, ecc...)
    rem_key = ""
    for k, v in client_loggati.items():
        if v == conn: rem_key = k
    if rem_key != "":
        client_loggati.pop(rem_key)
    
    print(Fore.RED + f"Client {addr} disconnesso...")


def user_checker():
    """
    Invio perpetuo degli utenti online: da usare in thread daemon per chiusura automatica con il server
    """

    while True:
        tm.sleep(float(5))
        with lock: #controllo con lock per risorsa condivisa tra thread
            for username, conn in client_loggati.items():
                others = [x for x in client_loggati if x != username]
                sendall(conn, pk.dumps(("U", others)))


def main():
    """
    Avvio del server di chat
    """

    #creazione della socket con indirizzo non bloccato
    server = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    server.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)

    try:
        #binding e limite attesa
        server.bind(ADDRESS)
        server.listen(4)
    except:
        print(Fore.RED + f"Associazione del server all'indirizzo {ADDRESS} fallita.")
        exit(0)
    
    print(Fore.BLUE + f"Server online all'indirizzo: {ADDRESS}")
    th.Thread(target=user_checker, daemon=True).start() #avvio del thread per il "send" degli utenti online

    while True:
        client = None
        #handle di ogni client
        try:
            client, indirizzo = server.accept()
            th.Thread(target=handle, args=(client, indirizzo), daemon=True).start()
        except KeyboardInterrupt:
            exit(0)


if __name__ == "__main__":
    main()
