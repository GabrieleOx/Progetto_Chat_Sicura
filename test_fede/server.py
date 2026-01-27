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
chats = {}     # chat_id -> (id1, id2)
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

def start_chat(a, b, sessionKey):
    global chats

    """
    Avvio della chat inviando la SK al destinatario
    
    :param a: ID del primo client
    :param b: ID del secondo client
    :param sessionKey: chiave di sessione simmetrica
    """

    with lock:
        if a not in client_loggati or b not in client_loggati:
            return

        #generazione nome della chat e controllo che non esista già con quel nome
        chat_id = str(random_words.get_random_word())
        while chat_id in chats.keys():
            chat_id = str(random_words.get_random_word())

        chats[chat_id] = (a, b)

        #invio della SK e conferma a chi l'ha creata
        sendall(client_loggati[a], pk.dumps(("O", [chat_id, b, True])))
        sendall(client_loggati[b], pk.dumps(("O", [chat_id, a, sessionKey]))) # True e False stanno per: hai startato tu?
        
def start_chat_MK(username, gruppo,sessionKey):
    global chats
    with lock:
        for n in gruppo:
            if n not in client_loggati:
                return 
    chat_id = str(random_words.get_random_word())
    while chat_id in chats.keys():
            chat_id = str(random_words.get_random_word())
    chats[chat_id] = (n for n in gruppo)
    countr = 0
    
    sendall(client_loggati[username], pk.dumps(("MO", [chat_id, gruppo, True]))) # True e False stanno per: hai startato tu?
    
    for n in gruppo:
        sendall(client_loggati[n], pk.dumps(("MO", [chat_id, [a for a in gruppo if n != a], sessionKey[countr]]))) # True e False stanno per: hai startato tu?
        
        
        countr += 1
        
        

def relay(chat_id, sender, text):
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
        
        if len(chats[chat_id]) > 2:
            gruppo = chats[chat_id]
            for n in gruppo:
                if sender!=n:
                    sendall(client_loggati[n], pk.dumps(("MM", [chat_id, sender, text])))
        else:
            a, b = chats[chat_id]
            target = b if sender == a else a
            if target in client_loggati:
                sendall(client_loggati[target], pk.dumps(("M", [chat_id, sender, text])))


def close_chat(chat_id):
    """
    Chiude la chat con l'ID specificato
    
    :param chat_id: ID del canale chat
    """

    with lock:
        if chat_id not in chats:
            return
        a, b = chats.pop(chat_id)

        # chiude da entrambi i lati, se non si sono già disconessi
        if a in client_loggati:
            sendall(client_loggati[a], pk.dumps(("C", chat_id)))
        if b in client_loggati:
            sendall(client_loggati[b], pk.dumps(("C", chat_id)))


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

def access(data: dict, conn_client: sk.socket) -> tuple[int] | tuple[int, bytes]:
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
                cur.execute("SELECT username, password FROM utente")
                utenti_pass = {row[0] : row[1] for row in cur.fetchall()}

                if username not in utenti_pass.keys():
                    return (1,)
                
                # e non sia già loggato
                if username in client_loggati.keys():
                    return (2,)
                
                #verifica della password
                if password_hash == utenti_pass[username]:
                    client_loggati[username] = conn_client
                    cur.execute("SELECT k.pvkey FROM user_key k JOIN utente u ON u.username = k.username WHERE u.username = ?", (username,))
                    conn.commit()
                    pvkey: bytes = cur.fetchone()[0]
                    return (0,pvkey)
                else: return (3,)
            except:
                return (4,)
    return (4,)



def request_key(username: str) -> tuple[int] | tuple[int, bytes]:
    """
    Richiesta della chiave pubblica dell'utente inserito
    
    :param username: username dell'utente di cui si chiede la PbK
    :type username: str
    :return: singolo codice di errore | codice di uscita e PbK
    :rtype: tuple[int] | tuple[int, bytes]
    """

    with db.connect(**db_params) as conn:
        with conn.cursor() as cur:

            try:
                #controllo che l'utente esista
                cur.execute("SELECT username, password FROM utente")
                utenti_pass = {row[0] : row[1] for row in cur.fetchall()}

                if username not in utenti_pass.keys():
                    return (1,)
                
                if username not in client_loggati.keys():
                    return (2,)

                cur.execute("SELECT pbkey FROM user_key WHERE username = ?", (username,))
                conn.commit()
                
                pbkey: bytes = cur.fetchone()[0]
                return (0, pbkey)
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

            case "MK":
                keys=[]
                for n in recived[1]:
                    keys.append(request_key(n))
                sendall(conn, pk.dumps(("MK", keys)))
            case "K":
                ex = request_key(recived[1])
                sendall(conn, pk.dumps(("K", ex)))
                
            case "MS":start_chat_MK(username,recived[1][0],recived[1][1])
                            
            case "S": start_chat(username, recived[1][0],recived[1][1])

            case "M": relay(recived[1][0], username, recived[1][1])

            case "C": close_chat(recived[1])


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
                        data_dict["private_key"] = ex[1]
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
