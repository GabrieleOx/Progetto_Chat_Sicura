import socket
import threading
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Vertical
from chat import ChatWindow
from colorama import Fore, init
import os
import signal

# Ignora Ctrl+C, così non chiude l'app
signal.signal(signal.SIGINT, signal.SIG_IGN)


def cls(): 
    os.system('cls' if os.name == 'nt' else 'clear')

init(autoreset=True)

HOST = "localhost"
PORT = 3000

COLORS = [Fore.CYAN, Fore.GREEN]

class ChatApp(App):
    CSS = "Static { height: 1fr; }"

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            self.main_display_text = "Comandi: LIST | CHAT <id>\n"
            self.main_display = Static(self.main_display_text)
            yield self.main_display
            self.main_input = Input(placeholder="> Inserisci comando")
            yield self.main_input
        yield Footer()

    def on_mount(self):
        self.sock = socket.socket()
        self.sock.connect((HOST, PORT))
        self.client_id = None
        self.chat_windows = {}  # chat_id -> ChatWindow
        self.chat_colors = {}   # chat_id -> {client_id: colore}
        threading.Thread(target=self.listen, daemon=True).start()

    def listen(self):
        buffer = ""
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                buffer += data.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        self.call_from_thread(self.handle, line)
            except:
                break
        self.call_from_thread(self.exit)

    def handle(self, msg):
        if msg.startswith("ID;"):
        
            _, cid = msg.split(";", 1)
            self.client_id = cid
            self.main_display_text += f"Il tuo ID: {cid}\n"
            self.main_display.update(self.main_display_text)

        elif msg.startswith("USERS;"):
            cls()
            self.main_display_text = "Comandi: LIST | CHAT <id>\n"
            users = msg.split(";")[1:]
            self.main_display_text += "Utenti connessi:\n"
            for u in users:
                self.main_display_text += f"- {u}\n"
            self.main_display.update(self.main_display_text)

        elif msg.startswith("START;"):
            _, chat_id, peer_id = msg.split(";", 2)
            if chat_id not in self.chat_windows:
                chat = ChatWindow(chat_id, peer_id, self.sock)
                chat._client_id = self.client_id
                self.chat_windows[chat_id] = chat
                self.mount(chat)
                chat.input.focus()



        elif msg.startswith("MSG;"):
            _, chat_id, sender_id, text = msg.split(";", 3)
            if chat_id in self.chat_windows:
                self.chat_windows[chat_id].receive_message(sender_id, text)

        elif msg.startswith("CLOSE;"):
            _, chat_id = msg.split(";", 1)
            if chat_id in self.chat_windows:
                self.chat_windows[chat_id].remove()
                del self.chat_windows[chat_id]

    def on_input_submitted(self, event):
        text = event.value.strip()
        event.input.value = ""
        if text.upper() == "LIST":
            try:
                self.sock.sendall(b"LIST\n")
            except:
                self.main_display_text += "Errore: connessione persa\n"
                self.main_display.update(self.main_display_text)

        elif text.upper().startswith("CHAT"):
            parts = text.split()
            if len(parts) == 2:
                try:
                    self.sock.sendall(f"CHAT;{parts[1]}\n".encode())
                except:
                    self.main_display_text += f"Errore: impossibile avviare chat con {parts[1]}\n"
                    self.main_display.update(self.main_display_text)
            else:
                self.main_display_text += "Errore: devi specificare l'ID del client\n"
                self.main_display.update(self.main_display_text)

        else:
            self.main_display_text += f"Comando sconosciuto: {text}\n"
            self.main_display.update(self.main_display_text)


if __name__ == "__main__":
    ChatApp().run()
