from colorama import Fore, init #pip install colorama 
import pickle as pk
import socket as sk
import mariadb as db #pip install mariadb
import threading as th

client_list = []
db_params = {
    "user" : "progetto_chat",
    "password" : "password-server", #queste credenziali sono per il mio database locale...
    "host" : "localhost",
    "database" : "progetto_chat_sicura"
}

def registration(data:dict) -> int:
    """
    Docstring for registration
    
    :param data: dati da inserire nel db
    :type data: dict
    :return: 0 tutto ok, 1 errore: utente già presente, 2 errore: errore nell'insermento
    :rtype: int
    """

    with db.connect(**db_params) as conn:
        with conn.cursor() as cur:

            #controllo che l'utente non esista già
            cur.execute("SELECT username FROM utente")
            utenti = [row[0] for row in cur.fetchall()]
            if data["username"] in utenti:
                return 1
            try:
                #inserisco i dati
                if "nome" in data.keys():
                    if "cognome" in data.keys():
                        cur.execute("INSERT INTO utente (username, password, nome, cognome) VALUES (?, ?, ?, ?)", (data["username"], data["password_hash"], data["nome"], data["cognome"]))
                    else:
                        cur.execute("INSERT INTO utente (username, password, nome) VALUES (?, ?, ?)", (data["username"], data["password_hash"], data["nome"]))
                else:
                    if "cognome" in data.keys():
                        cur.execute("INSERT INTO utente (username, password, cognome) VALUES (?, ?, ?)", (data["username"], data["password_hash"], data["cognome"]))
                    else:
                        cur.execute("INSERT INTO utente (username, password) VALUES (?, ?)", (data["username"], data["password_hash"]))
                conn.commit()
                #inserisco le chiavi
                cur.execute("INSERT INTO user_key (username, pbkey, pvkey) VALUES (?, ?, ?)", (data["username"], data["public_key"], data["private_key"]))
                conn.commit()
            except:
                cur.execute("DELETE FROM utente WHERE username = ?", (data["username"]))
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
                    ex = registration(recived[1])
                    conn.send(pk.dumps(("R", ex)))
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