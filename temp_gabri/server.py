from colorama import Fore, init #pip install colorama 
import pickle as pk
import socket as sk
import mariadb as db #pip install mariadb
import threading as th

client_list = []
client_lggati = {} # username : connessione al client

db_params = {
    "user" : "progetto_chat",
    "password" : "password-server", #queste credenziali sono per il mio database locale...
    "host" : "localhost",
    "database" : "progetto_chat_sicura"
}

def access(data: dict, conn_client: sk.socket) -> tuple[int] | tuple[int, bytes]:
    """
    Docstring for access
    
    :param data: dati da verificare col db
    :type data: dict
    :return: 0: loggato correttamente, 1: errore utente inesistente, 2: errore utente già loggato, 3: errore password errata
    :rtype: int
    """
    global client_lggati
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
                
                if username in client_lggati.keys():
                    return (2,)
                
                if password_hash == utenti_pass[username]:
                    client_lggati[username] = conn_client
                    cur.execute("SELECT k.pvkey FROM user_key k JOIN utente u ON u.username = k.username WHERE u.username = ?", (username,))
                    conn.commit()
                    pvkey: bytes = cur.fetchone()[0]
                    return (0,pvkey)
                else: return (3,)
            except:
                return (4,)
    return (4,)

def registration(data: dict) -> int:
    """
    Docstring for registration
    
    :param data: dati da inserire nel db
    :type data: dict
    :return: 0: tutto ok, 1: errore utente già presente, 2: errore nell'insermento dei dati
    :rtype: int
    """

    username = data["username"]
    password_hash = data["password_hash"]
    private_key = data["private_key"]
    public_key = data["public_key"]

    with db.connect(**db_params) as conn:
        with conn.cursor() as cur:

            try:
                #controllo che l'utente non esista già
                cur.execute("SELECT username FROM utente")
                utenti = [row[0] for row in cur.fetchall()]
                if username in utenti:
                    return 1
                
                #inserisco i dati
                if "nome" in data.keys():
                    if "cognome" in data.keys():
                        cur.execute("INSERT INTO utente (username, password, nome, cognome) VALUES (?, ?, ?, ?)", (username, password_hash, data["nome"], data["cognome"]))
                    else:
                        cur.execute("INSERT INTO utente (username, password, nome) VALUES (?, ?, ?)", (username, password_hash, data["nome"]))
                else:
                    if "cognome" in data.keys():
                        cur.execute("INSERT INTO utente (username, password, cognome) VALUES (?, ?, ?)", (username, password_hash, data["cognome"]))
                    else:
                        cur.execute("INSERT INTO utente (username, password) VALUES (?, ?)", (username, password_hash))
                conn.commit()
                #inserisco le chiavi
                cur.execute("INSERT INTO user_key (username, pbkey, pvkey) VALUES (?, ?, ?)", (username, public_key, private_key))
                conn.commit()
            except:
                cur.execute("DELETE FROM utente WHERE username = ?", (username,))
                conn.commit()
                return 2
    
    return 0


def manage_client(conn: sk.socket, addr):
    global client_list

    print(Fore.GREEN + f"Connesso {addr}")

    while True:
        try:
            recived = conn.recv(3072) #valore alto per tranquillità
            if not recived:
                break

            recived = pk.loads(recived)

            match recived[0]:
                case "R": 
                    code = registration(recived[1])
                    conn.send(pk.dumps(("R", code)))
                case "L":
                    ex = access(recived[1], conn)            
                    data_dict = {
                        "code" : ex[0]
                    }
                    if ex[0] == 0:
                        client_lggati[recived[1]["username"]] = conn
                    if len(ex) == 2:
                        data_dict["private_key"] = ex[1]
                    conn.send(pk.dumps(("L", data_dict)))
        except:
            break
    
    conn.close()
    client_list.remove((conn, addr)) # Disconnessione sicura
    print(Fore.RED + f"Client {addr} disconnesso...")

def main():
    global client_list

    init(autoreset=True)

    address = ("localhost", 6789)
    server = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    server.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1) #opzioni per socket generica TCP/UDP | address riutilizzabile | abilitato
    
    try:
        server.bind(address)
        server.listen(4) #massimo 4 disp in coda per essere accettati
    except:
        print(Fore.RED + f"Associazione del server all'indirizzo {address} fallita.")
        exit(0)

    print(Fore.BLUE + f"Server in ascolto all'indirizzo {address}:")
    while True:
        client = server.accept()
        client_list.append(client)
        th.Thread(target=manage_client, args=client).start()

if __name__ == "__main__":
    main()