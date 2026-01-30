import pickle as pk #per gestire un dizionario codificato in bytes
import socket as sk
import threading as th
import time as tm
import struct as st
from tkinter import colorchooser
from tkinter import Tk

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


#pip install pycryptodome: libreria per SECURITY
from Crypto.PublicKey import RSA #docs RSA: https://pycryptodome.readthedocs.io/en/latest/src/public_key/rsa.html
from Crypto.Hash import SHA256
from Crypto.Util.number import long_to_bytes, bytes_to_long
from Crypto.Cipher import AES #docs per la mode GCM: https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html#gcm-mode

#pip install textual: libreria per UI
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Vertical

import base64
import json

ADDRESS = ("localhost", 3000)

class ChatApp(App):
    CSS = "Static { height: 1fr; }"

    # ================= TUI =================
    def compose(self) -> ComposeResult: #Prima funzione che si avvia e costruisce il Textual
        yield Header()
        with Vertical():
            self.output = Static("", markup=True)
            yield self.output
            self.input = Input(placeholder="> ")
            yield self.input
        yield Footer()

    def on_mount(self): #Funzione "main"

        #connessione al server
        self.sock = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        try:
            self.sock.connect(ADDRESS)
        except:
            #connessione al server fallita
            exit(0)
        #connessione riuscita

        self.mode = "dislogged"
        self.text_shown: str = ""

        #dati per la registrazione
        self.registering = False
        self.user_to_register: str = ""
        self.pass_to_register: str = ""
        self.name_to_register: str = ""
        self.surname_to_register: str = ""
        self.color_to_register: str = ""

        #dati per il login
        self.logging = False
        self.client_username: str = ""
        self.my_password: str = ""

        #dopo il login
        self.logged = False
        self.current_chat = None
        self.my_color: str = ""
        self.private_key: RSA.RsaKey | None = None
        self.new_sk: bytes | None = None
        self.users_to_connect: list[str] = []
        self.users_to_add: list[str] = []

        self.users = []  # utenti connessi ??
        self.chats = {}  # chat_id -> {peers, messages[], sessionKey}

        self.render_dislogged_menu()
        th.Thread(target=self.listen, daemon=True).start()

    # ================= NETWORK =================
    def listen(self):
        """
        Funzione di ascolto sulla socket del client
        
        """

        while True:
            try:
                data = recv(self.sock)
                if not data:
                    break

                recived = pk.loads(data)

                self.call_from_thread(self.handle, recived)
            except:
                break

    def handle(self, recived): #dopo l'avvio del thread (on_mount)
        """
        Funzione per la gestione dei messaggi ricevuti
        
        :param recived: dati ricevuto
        """

        data = recived[1]

        match recived[0]:
            case "R":
                match data:
                    case 0:
                        self.user_to_register = ""
                        self.pass_to_register = ""
                        self.name_to_register = ""
                        self.surname_to_register = ""
                        self.registering = False
                        self.render_dislogged_menu()

                    case 1: self.output.update(self.text_shown + f"\n[red]Registrazione fallita, utente con username: {self.user_to_register} già presente\ncode: {recived[1]}[/red]")
                    case 2: self.output.update(self.text_shown + f"\n[red]Registrazione fallita, errore nell'inserimento dei dati\ncode: {recived[1]}[/red]")
            
            case "L":
                match data["code"]:
                    case 0:
                        self.private_key = RSA.import_key(data["private_key"], self.my_password)
                        self.my_color = data["colore"]
                        self.logging = False
                        self.logged = True
                        self.render_logged_menu()
                    
                    case 1: self.output.update(self.text_shown + f"\n[red]Login fallito, utente '{self.client_username}' inesistente\ncode: {data["code"]}[/red]")
                    case 2: self.output.update(self.text_shown + f"\n[red]Login fallito, utente '{self.client_username}' già loggato\ncode: {data["code"]}[/red]")
                    case 3: self.output.update(self.text_shown + f"\n[red]Login fallito, password errata\ncode: {data["code"]}[/red]")
                    case 4: self.output.update(self.text_shown + f"\n[red]Login fallito, errore nel controllo dei dati utente\ncode: {data["code"]}[/red]")

            case "K":
                match data[0]:
                    case 0:
                        try:
                            keys_to_connect: dict[str, RSA.RsaKey] = {}
                            checking = "" #tengo l'utente che sto importando per scriverlo in caso di errori....

                            try:
                                for usr, key in data[1].items():
                                    checking = usr
                                    keys_to_connect[usr] = RSA.import_key(key)
                            except:
                                self.output.update(self.text_shown + f"\n[red]Errore nella lettura della chiave pubblica di {checking}...[/red]")
                                return #chiudo in caso di errore
                            
                            #creazione chiave di sessione \/
                            sessionKey = createHashForChat(self.client_username, self.my_password)
                            self.new_sk = sessionKey

                            #cifratura chiave di sessione \/
                            cifrate: dict[str, bytes | bool] = {
                                self.client_username : True #di base metto il "sender"
                            }
                            for usr, key in keys_to_connect.items():

                                encrypted = cryptWithPublic(
                                    sessionKey,
                                    key
                                )
                                cifrate[usr] = encrypted
                            
                            #invio tutto:
                            sendall(self.sock, pk.dumps(("S", cifrate))) #invio un dizionario: nomi -> chiavi cifrate
                            
                        except:
                            self.output.update(self.text_shown + f"\n[red]Errore nell'invio delle chiavi di sessione...[/red]")
                    case 1: self.output.update(self.text_shown + f"\n[red]Errore utente: uno o più utenti non esistono...[/red]")
                    case 2: self.output.update(self.text_shown + f"\n[red]Errore utente: uno o più utenti sono offline...[/red]")
                    case 3: self.output.update(self.text_shown + f"\n[red]Errore nella richiesta della chiave pubblica degli utenti richiesti...[/red]")

            case "AK": #caso in cui sto aggiungendo utenti ad una chat
                keys = data["keys"]
                chat = data["chat_id"]

                match keys[0]: #controllo come nel caso di "K"
                    case 0:
                        try:
                            keys_to_connect: dict[str, RSA.RsaKey] = {}
                            checking = "" #tengo l'utente che sto importando per scriverlo in caso di errori....

                            try:
                                for usr, key in keys[1].items():
                                    checking = usr
                                    keys_to_connect[usr] = RSA.import_key(key)
                            except:
                                self.output.update(self.text_shown + f"\n[red]Errore nella lettura della chiave pubblica di {checking}...[/red]")
                                return #chiudo in caso di errore
                            
                            #if chat in self.chats.keys():
                                #return #caso "strano" non esiste la chat a cui aggiungere utenti????
                            
                            sessionKey = self.chats[chat]["sessionKey"]

                            criptate: dict[str, bytes] = {}

                            for usr, key in keys_to_connect.items():

                                encrypted = cryptWithPublic(
                                    sessionKey,
                                    key
                                )
                                criptate[usr] = encrypted
                            #ho le chiavi cifrate
                            sendall(self.sock, pk.dumps(("A", {"chat" : chat, "keys" : criptate})))
                            
                        except:
                            self.output.update(self.text_shown + f"\n[red]Errore nell'invio delle chiavi di sessione...[/red]")
                    case 1: self.output.update(self.text_shown + f"\n[red]Errore utente: uno o più utenti non esistono...[/red]")
                    case 2: self.output.update(self.text_shown + f"\n[red]Errore utente: uno o più utenti sono offline...[/red]")
                    case 3: self.output.update(self.text_shown + f"\n[red]Errore nella richiesta della chiave pubblica degli utenti richiesti...[/red]")

            case "A":
                chat_id, peers = data

                if chat_id not in self.chats.keys():
                    return

                self.chats[chat_id]["peers"] = peers
                self.render_logged_menu()

            case "U":
                self.users = data
                if self.mode == "logged":
                    self.render_logged_menu()
            case "O":
                chat_id, peers, encoded_or_me = data
                
                if isinstance(encoded_or_me, bytes):
                    if self.private_key is not None:
                        sessionKey = decryptWithPrivate(
                            encoded_or_me,
                            self.private_key
                        )
                elif isinstance(encoded_or_me, bool) and encoded_or_me:
                    if self.new_sk is not None:
                        sessionKey = self.new_sk
                        self.new_sk = None

                #if chat_id not in self.chats:  --> Ho tolto il controllo perchè viene gestito dal server.... REM: Errore e cancellazione chat
                self.chats[chat_id] = {"peers": peers, "messages": [], "sessionKey": sessionKey}
                self.notify(f"chat avviata con {", ".join(u for u in peers)}")
                self.render_logged_menu()

            case "M":
                chat_id, sender, text, colore_altro = data
                if chat_id in self.chats:
                    name = "Tu" if sender == self.client_username else sender
                    color = self.my_color if sender == self.client_username else colore_altro
                    self.chats[chat_id]["messages"].append(f"[{color}]{name}: {text}[/]")

                    if self.mode!="chat" or not self.current_chat == chat_id: #notifica
                        self.notify(f"Nuovo messaggio ricevuto da {sender}")

                    if self.mode == "chat" and self.current_chat == chat_id:
                        self.render_chat(chat_id)
            case "C":
                chat_id = data
                self.chats.pop(chat_id, None)
                if self.current_chat == chat_id:
                    self.mode = "menu"
                    self.current_chat = None
                    self.render_logged_menu()

    # ================= UI =================
    def render_dislogged_menu(self):
        """
        Renderizzazione della UI del menu di un utente non loggato

        """

        self.mode = "dislogged"

        text = "[yellow]=== COMANDI ===[/]\n"
        text += "REGISTER   → crea il tuo utente\n"
        text += "LOGIN      → entra nel tuo account\n"
        text += "EXIT       → esci\n"

        self.text_shown = text
        self.output.update(text)

    def render_logged_menu(self):
        """
        Renderizzazione della UI del menu di un utente loggato

        """

        self.mode = "logged"

        text = "[yellow]=== COMANDI ===[/]\n"
        text += "CHAT <usernames>    → avvia chat\n"
        text += "OPEN <chat_id>      → entra in chat\n"
        text += "CLOSE <chat_id>     → chiudi chat\n"
        text += "LOGOUT              → esci dall'account\n"
        text += "P.S: ESATTAMENTE UNO SPAZIO TRA KEYWORD E ID\nO TRA GLI USERNAMES PER LA CHAT\n\n"
        if self.client_username:
            text += f"[yellow]Il tuo username:[/] {self.client_username}\n\n"

        text += "\n[yellow]=== UTENTI CONNESSI ===[/]\n"
        if self.users:
            for u in self.users:
                text += f"- {u}\n"
        else:
            text += "Nessun altro utente\n"
        text += "\n"

        text += "[yellow]=== CHAT ATTIVE ===[/]\n"
        if self.chats:
            for cid, c in self.chats.items():
                text += f"- {cid} (con {", ".join(user for user in c['peers'])})\n"
        else:
            text += "Nessuna chat attiva\n"

        self.text_shown = text
        self.output.update(text)

    def render_registration(self):
        """
        Renderizzazione della UI di registrazione

        """

        testo =  "[green]Registrazione:[/green]\n\n"
        testo += "[yellow]=== COMANDI ===[/yellow]\n"
        testo += "USERNAME <username>     → username del nuovo utente\n"
        testo += "PASSWORD <password>     → password del nuovo utente\n"
        testo += "COLOR                   → scegli il tuo colore nelle chat\n"
        testo += "NOME <nome>             → nome del nuovo utente (opzionale)\n"
        testo += "COGNOME <cognome>       → cognome del nuovo utente (opzionale)\n"
        testo += "SEND                    → invia i dati\n\n"
        testo += "EXIT                    → torna al menu\n\n"
        testo += f"[yellow]USERNAME INSERITO:[/yellow]  {self.user_to_register}\n"
        testo += f"[yellow]PASSWORD INSERITA:[/yellow]  {self.pass_to_register}\n"
        testo += f"[yellow]NOME INSERITO:[/yellow]  {self.name_to_register}\n"
        testo += f"[yellow]COGNOME INSERITO:[/yellow]  {self.surname_to_register}\n"

        self.registering = True
        self.text_shown = testo
        self.output.update(testo)

    def render_login(self):
        """
        Renderizzazione della UI di login

        """

        testo =  "[green]Login:[/green]\n\n"
        testo += "[yellow]=== COMANDI ===[/yellow]\n"
        testo += "USERNAME <username>     → username\n"
        testo += "PASSWORD <password>     → password\n"
        testo += "SEND                    → invia i dati\n\n"
        testo += "EXIT                    → torna al menu\n\n"
        testo += f"[yellow]USERNAME INSERITO:[/yellow]  {self.client_username}\n"
        testo += f"[yellow]PASSWORD INSERITA:[/yellow]  {self.my_password}\n"

        self.logging = True
        self.text_shown = testo
        self.output.update(testo)

    def render_chat(self, chat_id):
        """
        Renderizzazione della UI della chat
        
        :param chat_id: ID della chat
        """

        chat = self.chats[chat_id]
        key = chat["sessionKey"]

        text = f"[yellow]Chat con {", ".join(user for user in chat['peers'])} [{chat_id}][/]\n"
        text += "-" * 40 + "\n"

        for msg in chat["messages"]:
            if msg.startswith(f"[{self.my_color}]Tu: "):
                payload = msg.replace(f"[{self.my_color}]Tu: ", "").replace("[/]", "")
                plain = simmetricDecryption(payload, key)
                text += f"[{self.my_color}]Tu: {plain}[/]\n"
            else:
                sender, payload = msg.split(": ", 1)
                payload = payload.replace("[/]", "")
                plain = simmetricDecryption(payload, key)
                text += f"{sender}: {plain}\n"

        text += "\n[yellow]/add <usernames>[/] → chiudi chat\n"
        text += "[yellow]/exit[/]              → torna al menu\n"
        text += "[yellow]/close[/]             → chiudi chat\n"

        self.text_shown = text
        self.output.update(text)


    def login(self):
        """
        Login utente
        
        """

        #uso my password così se i log va bene rimane salvata
        password_hash = sha256(self.my_password.encode())

        dati_login = {
            "username" : self.client_username,
            "password_hash" : password_hash
        }

        to_send = pk.dumps(("L", dati_login))

        #li invio...
        sendall(self.sock, to_send)


    def signin(self):
        """
        Registrazione nuovo utente
        
        """

        password_hash = sha256(self.pass_to_register.encode())

        #generazione chiavi RSA:

        new_key = RSA.generate(3072)
        public = new_key.public_key().export_key(format="DER") #DER per averla direttamente in binario
        private = new_key.export_key(format="DER", passphrase=self.pass_to_register, pkcs=8) # è possibile renderla ancora più sicura con: protection="PBKDF2WithHMAC-SHA512AndAES256-CBC"

        #popolo il dizionario da inviare
        data_dict = {
            "username" : self.user_to_register,
            "password" : password_hash,
            "colore" : self.color_to_register,
            "pbkey" : public,
            "pvkey" : private
        }

        if self.name_to_register != "":
            data_dict["nome"] = self.name_to_register
        if self.surname_to_register != "":
            data_dict["cognome"] = self.surname_to_register
        
        to_send = pk.dumps(("R", data_dict)) # "R" per registrazione e pickle per averli encoded

        sendall(self.sock, to_send)


    # ================= INPUT =================
    def on_input_submitted(self, event):
        """
        Lettura dell'input utente
        
        :param event: lettore dell'evento "invio"
        """

        text = event.value.strip()
        event.input.value = ""

        match self.mode:
            case "logged": self.handle_logged_menu_input(text)
            case "dislogged": self.handle_dislogged_menu_input(text)
            case "chat": self.handle_chat_input(text)


    def handle_dislogged_menu_input(self, text: str):
        """
        Funzione per gestire l'input quando nel menu di un utente non loggato
        
        :param text: testo inserito dall'utente
        :type text: str
        """

        match text.upper():
            case "REGISTER":
                if not self.registering and not self.logging:
                    self.render_registration()

            case "LOGIN":
                if not self.registering and not self.logging:
                    self.render_login()

            case "SEND":
                if self.registering:
                    if self.user_to_register == "" or self.pass_to_register == "":
                        self.output.update(self.text_shown + "\n[red]Username e/o Password mancanti...[/red]")
                    else:
                        self.signin()
                elif self.logging:
                    if self.client_username == "" or self.my_password == "":
                        self.output.update(self.text_shown + "\n[red]Username e/o Password mancanti...[/red]")
                    else:
                        self.login()

            case "COLOR":
                if self.registering:
                    self.color_to_register = get_hex_color()

            case "EXIT":
                if self.registering:
                    #riporto tutte le variabili a None \/
                    self.registering = False
                    self.pass_to_register = ""
                    self.user_to_register = ""
                    self.render_dislogged_menu()

                elif self.logging:
                    #riporto tutte le variabili a None \/
                    self.logging = False
                    self.client_username = ""
                    self.my_password = ""
                    self.render_dislogged_menu()
                
                else: exit(0)

            case _:
                if text.startswith(("USERNAME ", "username ")):
                    if self.registering:
                        self.user_to_register = text.split(" ", 1)[1].strip()
                        self.render_registration()

                    elif self.logging:
                        self.client_username = text.split(" ", 1)[1].strip()
                        self.render_login()

                elif text.startswith(("PASSWORD ", "password ")):
                    if self.registering:
                        self.pass_to_register = text.split(" ", 1)[1].strip()
                        self.render_registration()

                    elif self.logging:
                        self.my_password = text.split(" ", 1)[1].strip()
                        self.render_login()

                elif text.startswith(("NOME ", "nome ")):
                    if self.registering:
                        self.name_to_register = text.split(" ", 1)[1].strip()
                        self.render_registration()

                elif text.startswith(("COGNOME ", "cognome ")):
                    if self.registering:
                        self.surname_to_register = text.split(" ", 1)[1].strip()
                        self.render_registration()

    def handle_logged_menu_input(self, text: str):
        """
        Funzione per gestire l'input quando nel menu di un utente loggato
        
        :param text: testo inserito dall'utente
        :type text: str
        """
        
        if text.upper() == "LOGOUT":
            if self.logged:
                    sendall(self.sock, pk.dumps(("E", self.client_username)))
                    self.client_username = ""
                    self.logged = False
                    self.private_key = None
                    self.render_dislogged_menu()

        elif text.startswith(("CHAT ", "chat ")):
            self.users_to_connect = [name.strip() for name in text.split(" ")[1:] if name not in ("", " ")]
            #chiedo le pubbliche
            sendall(self.sock, pk.dumps(("K", self.users_to_connect)))

        elif text.startswith(("OPEN ", "open ")):
            _, chat_id = text.split(" ", 1)
            if chat_id in self.chats:
                self.mode = "chat"
                self.current_chat = chat_id
                self.render_chat(chat_id)

        elif text.startswith(("CLOSE ", "close ")):
            _, chat_id = text.split(" ", 1)
            if chat_id in self.chats:
                sendall(self.sock, pk.dumps(("C", chat_id)))
                self.chats.pop(chat_id, None)
                self.render_logged_menu()
            

    def handle_chat_input(self, text: str):
        """
        Funzione per gestire l'input quando in una chat
        
        :param text: testo inserito dall'utente
        :type text: str
        """

        chat_id = self.current_chat
        key = self.chats[chat_id]["sessionKey"]

        if text == "/exit":
            self.mode = "menu"
            self.current_chat = None
            self.render_logged_menu()

        elif text == "/close":
            sendall(self.sock, pk.dumps(("C", chat_id)))
            self.chats.pop(chat_id, None)
            self.mode = "menu"
            self.current_chat = None
            self.render_logged_menu()

        elif text.startswith("/add "):
            self.users_to_add = [name.strip() for name in text.split(" ")[1:] if name not in ("", " ")]
            #chiedo le pubbliche
            sendall(self.sock, pk.dumps(("K", self.users_to_add, "A", chat_id)))

        else:
            cipher = simmetriCryption(text.strip(), key)
            self.chats[chat_id]["messages"].append(f"[{self.my_color}]Tu: {cipher}[/]")
            sendall(self.sock, pk.dumps(("M", [chat_id, cipher, self.my_color])))
            self.render_chat(chat_id)

# ================= AES =================
def simmetriCryption(plainText, key):
    """
    Funzione per criptare un messaggio con una chiave simmetrica AES-GCM
        
    :param plainText: messaggio in chiaro da cifrare
    :param key: chiave simmetrica con cui cifrare
    """

    header = b"header"
    data = plainText.encode()
    cipher = AES.new(key, AES.MODE_GCM)
    cipher.update(header)
    ciphertext, tag = cipher.encrypt_and_digest(data)

    json_k = ['nonce', 'header', 'ciphertext', 'tag']
    json_v = [base64.b64encode(x).decode('utf-8') for x in (cipher.nonce, header, ciphertext, tag)]
    return json.dumps(dict(zip(json_k, json_v)))    

def simmetricDecryption(cipherText, key):
    """
    Funzione per decriptare con payload e chiave simmetrica AES-GCM
    
    :param cipherText: payload cifrato con AES-GCM
    :param key: chiave simmetrica con cui decifrare
    """

    try:
        b64 = json.loads(cipherText)
        json_k = ['nonce', 'header', 'ciphertext', 'tag']
        jv = {k: base64.b64decode(b64[k]) for k in json_k}
        cipher = AES.new(key, AES.MODE_GCM, nonce=jv['nonce'])
        cipher.update(jv['header'])
        plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
        return plaintext.decode('utf-8')
    except (ValueError, KeyError):
        return "Incorrect decryption"

# ================= RSA =================
def cryptWithPublic(data: bytes, public_key: RSA.RsaKey):
    """
    Funzione per criptare con una chiave pubblica RSA
    
    :param data: dati da criptare
    :type data: bytes
    :param public_key: chiave pubblica RSA
    :type public_key: RSA.RsaKey
    """

    m = bytes_to_long(data)
    c = pow(m, public_key.e, public_key.n)
    return long_to_bytes(c)

def decryptWithPrivate(cipherText: bytes, private_key: RSA.RsaKey):
    """
    Funzione per decriptare con una chiave privata RSA
    
    :param cipherText: testo cifrato
    :type cipherText: bytes
    :param private_key: chiave privata RSA
    :type private_key: RSA.RsaKey
    """

    c = bytes_to_long(cipherText)
    m = pow(c, private_key.d, private_key.n)
    return long_to_bytes(m)

def sha256(value: bytes | bytearray) -> bytes:
    """
    Funzione per hash sha256
    
    :param value: dati da hashare
    :type value: bytes | bytearray
    :return: hash dei dati passati
    :rtype: bytes
    """

    hasher = SHA256.new()
    hasher.update(value)
    return hasher.digest()

def createHashForChat(usr: str, password: str):
    """
    Funzione per la generazione di Session Keys:
    Hash( Hash( nome ) + Hash( password ) + Hash( time ) )
    
    :param usr: nome utente
    :type usr: str
    :param password: password utente
    :type password: str
    """

    global timestamp
    timestamp=int(tm.time())
    to_hash=str(sha256(usr.encode()))+str(sha256(password.encode()))+str(timestamp)
    return sha256(to_hash.encode())

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

#coolori:
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_hex_color() -> str:
    root = Tk()
    root.withdraw()  

    while True:
        color = colorchooser.askcolor(title="Scegli un colore valido (abbastanza visibile...)")[0]

        if color:
            hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}".upper()
        else:
            continue #nessun colore selezionato

        if color is not None:
            rgb=hex_to_rgb(f"{color[0]:02x}{color[1]:02x}{color[2]:02x}")

        luminanza = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        
        if(luminanza>=100):
            return hex_color

if __name__ == "__main__":
    ChatApp().run()
