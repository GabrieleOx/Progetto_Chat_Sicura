import uuid
from colorama import Fore, init #pip install colorama 
import pickle as pk
import socket as sk
import mariadb as db #pip install mariadb
import threading as th

ADDRESS = ("localhost", 3000)

client_loggati: dict[str, sk.socket] = {} # username : connessione al client
chats = {}     # chat_id -> (id1, id2)
lock = th.Lock()

db_params = {
    "user" : "progetto_chat",
    "password" : "password-server", #queste credenziali sono per il mio database locale...
    "host" : "localhost",
    "database" : "progetto_chat_sicura"
}


def broadcast_users():
    with lock:
        for username, conn in client_loggati.items():
            others = [x for x in client_loggati if x != username]
            conn.send(pk.dumps(("U", others))) #USERS = U


def start_chat(a, b, sessionKey):
    global chats

    """
    Docstring for start_chat
    
    :param a: ID del primo client
    :param b: ID del secondo client
    :param sessionKey: chiave di sessione simmetrica
    """

    with lock:
        if a not in client_loggati or b not in client_loggati:
            return

        chat_id = str(uuid.uuid4())[:8]
        chats[chat_id] = (a, b)
        
        print(f"a:{a}\nb:{b}\nloggati:{client_loggati}")

        client_loggati[a].send(pk.dumps(("O", [chat_id, b, sessionKey]))) # START = O like OPEN
        client_loggati[b].send(pk.dumps(("O", [chat_id, a, sessionKey])))


def relay(chat_id, sender, text):
    """
    Docstring for relay
    
    :param chat_id: id della chat
    :param sender: id di chi manda il messaggio
    :param text: messaggio
    """

    with lock:
        if chat_id not in chats:
            return
        a, b = chats[chat_id]
        target = b if sender == a else a
        if target in client_loggati:
            client_loggati[target].send(pk.dumps(("M", [chat_id, sender, text]))) # MSG = M


def close_chat(chat_id):
    with lock:
        if chat_id not in chats:
            return
        a, b = chats.pop(chat_id)
        if a in client_loggati:
            client_loggati[a].send(pk.dumps(("C", chat_id))) # CLOSE = C
        if b in client_loggati:
            client_loggati[b].send(pk.dumps(("C", chat_id)))












#new \/

def registration(data: dict) -> int:
    """
    Docstring for registration
    
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

                """if "nome" in data.keys():
                    if "cognome" in data.keys():
                        cur.execute("INSERT INTO utente (username, password, nome, cognome) VALUES (?, ?, ?, ?)", (username, password_hash, data["nome"], data["cognome"]))
                    else:
                        cur.execute("INSERT INTO utente (username, password, nome) VALUES (?, ?, ?)", (username, password_hash, data["nome"]))
                else:
                    if "cognome" in data.keys():
                        cur.execute("INSERT INTO utente (username, password, cognome) VALUES (?, ?, ?)", (username, password_hash, data["cognome"]))
                    else:
                        cur.execute("INSERT INTO utente (username, password) VALUES (?, ?)", (username, password_hash))
                conn.commit()"""
                #inserisco le chiavi
                cur.execute(f"INSERT INTO user_key ({",".join(str(key) for key in chiavi.keys())}) VALUES ({",".join("?" for i in range(len(chiavi)))})", tuple(chiavi[key] for key in chiavi.keys()))
                conn.commit()
            except:
                cur.execute("DELETE FROM utente WHERE username = ?", (username,))
                conn.commit()
                return 2
    
    return 0

def access(data: dict, conn_client: sk.socket) -> tuple[int] | tuple[int, bytes]:
    """
    Docstring for access
    
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
                
                if username in client_loggati.keys():
                    return (2,)
                
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
    broadcast_users()
    #da fare con pickle \/
    while True:
        data = conn.recv(8192)
        if not data:
            break
            
        recived = pk.loads(data)
        match recived[0]:
            #già da loggato \/
            case "E":
                username_remove = recived[1]
                client_loggati.pop(username_remove)
                broadcast_users()
                break #esce dall "modalità loggato"

            case "K":
                ex = request_key(recived[1])
                conn.send(pk.dumps(("K", ex)))

            case "S": start_chat(username, recived[1][0],recived[1][1]) #CHAT = S

            case "M": relay(recived[1][0], username, recived[1][1]) #MSG = M

            case "C": close_chat(recived[1]) #CLOSE = C


def handle(conn: sk.socket, addr):
    print(Fore.GREEN + f"Connesso {addr}")

    while True:
        try:
            recived = conn.recv(3072) #valore alto per tranquillità
            if not recived:
                break

            recived = pk.loads(recived)

            match recived[0]: #smista le richieste
                case "R": 
                    code = registration(recived[1])
                    conn.send(pk.dumps(("R", code)))
                case "L":
                    ex = access(recived[1], conn)            
                    data_dict: dict[str, int | bytes] = {
                        "code" : ex[0]
                    }
                    if ex[0] == 0:
                        client_loggati[recived[1]["username"]] = conn
                    if len(ex) == 2:
                        data_dict["private_key"] = ex[1]
                    conn.send(pk.dumps(("L", data_dict)))
                    if ex[0] == 0:
                        loggato(recived[1]["username"], conn)
        except:
            break
    
    conn.close() # Disconnessione sicura

    #sicurezza per chiusura processi \/
    rem_key = ""
    for k, v in client_loggati.items():
        if v == conn: rem_key = k
    if rem_key != "":
        client_loggati.pop(rem_key)
    
    broadcast_users()
    print(Fore.RED + f"Client {addr} disconnesso...")


def main():
    server = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    server.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)

    try:
        server.bind(ADDRESS)
        server.listen(4)
    except:
        print(Fore.RED + f"Associazione del server all'indirizzo {ADDRESS} fallita.")
        exit(0)
    
    print(Fore.BLUE + f"Server online all'indirizzo: {ADDRESS}")

    while True:
        client, indirizzo = server.accept()
        th.Thread(target=handle, args=(client, indirizzo), daemon=True).start()


if __name__ == "__main__":
    main()
