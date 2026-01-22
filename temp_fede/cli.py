import socket
import threading
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Vertical
import os
import hashlib
from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long,long_to_bytes
import pickle as pk
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
import base64
import json
from base64 import b64encode
from base64 import b64decode

HOST = "localhost"
PORT = 3000
sessionKey=0
prova=0
password="ciaooo122"

class ChatApp(App):
    CSS = "Static { height: 1fr; }"
    def simmetriCryption(self,plainText, key):
        header = b"header"
        data = plainText.encode()
        cipher = AES.new(key, AES.MODE_GCM)
        cipher.update(header)
        ciphertext, tag = cipher.encrypt_and_digest(data)

        json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
        json_v = [ b64encode(x).decode('utf-8') for x in (cipher.nonce, header, ciphertext, tag) ]
        result = json.dumps(dict(zip(json_k, json_v)))
        return result

    def simmetricDecryption(self,cipherText, key):
        try:
            b64 = json.loads(cipherText)
            json_k = [ 'nonce', 'header', 'ciphertext', 'tag' ]
            jv = {k:b64decode(b64[k]) for k in json_k}
            cipher = AES.new(key, AES.MODE_GCM, nonce=jv['nonce'])
            cipher.update(jv['header'])
            plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['tag'])
            return plaintext.decode('utf-8')
        except (ValueError, KeyError):
            return "Incorrect decryption"

    def cryptWithPublic(self,data: bytes, path: str):
        public_key_data = open(path,"rb").read()
        pub = RSA.import_key(public_key_data)

        m = bytes_to_long(data)
        c = pow(m, pub.e, pub.n)
        return long_to_bytes(c)

    def decryptWithPrivate(self,cipherText: bytes, path: str):
        c = bytes_to_long(cipherText)

        private_key_data = open(path,"rb").read()
        pvt = RSA.import_key(private_key_data, passphrase=password)

        m = pow(c, pvt.d, pvt.n)
        return long_to_bytes(m)

    def compose(self) -> ComposeResult: #funzione che crea la tui graficamente
        yield Header()
        with Vertical():
            self.output = Static("", markup=True)
            yield self.output
            self.input = Input(placeholder="> ")
            yield self.input
        yield Footer()

    def on_mount(self):  #funzione per settare gli stati della comunicazione evviare il thread che riceve messaggi
        self.sock = socket.socket()
        self.sock.connect((HOST, PORT))

        self.client_id = None
        self.mode = "menu"
        self.current_chat = None

        self.users = []
        self.chats = {}  # chat_id -> {peer, messages[],sessionKey}

        self.render_menu()

        threading.Thread(target=self.listen, daemon=True).start()

    # ================= NETWORK =================

    def listen(self): #thread che riceve messaggi, li decodifica e splitta in una lista (protocollo con ;)
        buffer = ""
        while True:
            try:
                data = self.sock.recv(8192)
                if not data:
                    break
                buffer += data.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.call_from_thread(self.handle, line.strip())
            except:
                break

    def handle(self, msg): #funzione per analizzare il tipo di messaggio (presente nel primo elemento della lista splittata)
        if msg.startswith("ID;"):
            self.client_id = msg.split(";", 1)[1]
            self.render_menu()

        elif msg.startswith("USERS;"):
            self.users = [u for u in msg.split(";")[1:] if u]
            self.render_menu(show_users=True)

        elif msg.startswith("START;"):
            _, chat_id, peer, encoded = msg.split(";", 3)

            encrypted = base64.b64decode(encoded)

            sessionKey = self.decryptWithPrivate(
                encrypted,
                "C:/Users/f9819/Desktop/private_corrente.der"
            )
            #self.output.update(sessionKey.hex())
            if chat_id not in self.chats: self.chats[chat_id] = { "peer": peer, "messages": [], "sessionKey":sessionKey }

            self.render_menu()

        elif msg.startswith("MSG;"):
            _, chat_id, sender, text = msg.split(";", 3)
            if chat_id in self.chats:
                name = "Tu" if sender == self.client_id else sender
                color = "cyan" if sender == self.client_id else "green"
                self.chats[chat_id]["messages"].append(
                    f"[{color}]{name}: {text}[/]"
                )
                if self.mode == "chat" and self.current_chat == chat_id:
                    self.render_chat(chat_id)

        elif msg.startswith("CLOSE;"):
            _, chat_id = msg.split(";", 1)
            self.chats.pop(chat_id, None)
            if self.current_chat == chat_id:
                self.mode = "menu"
                self.current_chat = None
                self.render_menu()

    # ================= UI =================

    def render_menu(self, show_users=False): #funzione per stampare il menù
        self.mode = "menu"

        text = "[yellow]=== COMANDI ===[/]\n"
        text += "CHAT <id>           → avvia chat\n"
        text += "OPEN <chat_id>      → entra in chat\n"
        text += "CLOSE <chat_id>     → chiudi chat\n"
        text +="P.S: ESATTAMENTE UNO SPAZIO TRA KEYWORD E ID \n\n"
        if self.client_id:
            text += f"[yellow]Il tuo ID:[/] {self.client_id}\n\n"

        text+= "\n[yellow]=== UTENTI CONNESSI ===[/]\n"
        if self.users:
                for u in self.users:
                    text += f"- {u}\n"
        else:
                text += "Nessun altro utente\n"
        text += "\n"

        text += "[yellow]=== CHAT ATTIVE ===[/]\n"
        if self.chats:
            for cid, c in self.chats.items():
                text += f"- {cid} (con {c['peer']})\n"
        else:
            text += "Nessuna chat attiva\n"

        self.output.update(text)

    def render_chat(self, chat_id): #funzione per stampare la chat
        chat = self.chats[chat_id]

        text = f"[yellow]Chat con {chat['peer']} [{chat_id}][/]\n"
        text += "-" * 40 + "\n"
        for i in range(0,len(self.chats[chat_id]["messages"])):
            self.chats[chat_id]["messages"][i]=self.simmetricDecryption(self.chats[chat_id]["messages"][i],sessionKey)
        for m in chat["messages"]:
            text += m + "\n"

        text += "\n[yellow]/exit[/] → torna al menu\n"
        text += "[yellow]/close[/] → chiudi chat\n"

        self.output.update(text)

    # ================= INPUT =================

    def on_input_submitted(self, event): #funzione per gestire gli input
        text = event.value.strip()
        event.input.value = ""

        if self.mode == "menu":
            self.handle_menu_input(text)
        else:
            self.handle_chat_input(text)

    def handle_menu_input(self, text): #gestione tipo input menù
        global sessionKey

        if text.startswith("CHAT "):
            
            sessionKey = get_random_bytes(32)

            encrypted = self.cryptWithPublic(
                sessionKey,
                "C:/Users/f9819/Desktop/public_corrente.der"
            )

            encoded = base64.b64encode(encrypted).decode()
            _, uid = text.split(" ", 1)
            self.sock.sendall(f"CHAT;{uid};{encoded}\n".encode())
            #self.output.update(sessionKey.hex())
            

        elif text.startswith("OPEN "):
            _, chat_id = text.split(" ", 1)
            if chat_id in self.chats:
                self.mode = "chat"
                self.current_chat = chat_id
                self.render_chat(chat_id)

        elif text.startswith("CLOSE "):
            _, chat_id = text.split(" ", 1)
            if chat_id in self.chats:
                self.sock.sendall(f"CLOSE;{chat_id}\n".encode())
                self.chats.pop(chat_id, None)
                self.render_menu()

    def handle_chat_input(self, text): #gestione chat singola
        chat_id = self.current_chat

        if text == "/exit":
            self.mode = "menu"
            self.current_chat = None
            self.render_menu()

        elif text == "/close":
            self.sock.sendall(f"CLOSE;{chat_id}\n".encode())
            self.chats.pop(chat_id, None)
            self.mode = "menu"
            self.current_chat = None
            self.render_menu()

        else:
            text=self.simmetriCryption(text,sessionKey)
            self.chats[chat_id]["messages"].append(
                f"[cyan]Tu: {text}[/]"
            )
            self.sock.sendall(f"MSG;{chat_id};{text}\n".encode())
            self.render_chat(chat_id)


if __name__ == "__main__":
    ChatApp().run()
