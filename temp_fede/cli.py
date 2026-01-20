import socket
import threading
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Vertical
from chat import ChatWindow

HOST = "localhost"
PORT = 3000

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
        self.chat_windows = {}  # chat_id -> ChatWindow
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
        users = msg.split(";")[1:]
        if users:
            self.main_display_text += "Utenti connessi:\n" + "\n".join(users) + "\n"
        else:
            self.main_display_text += "Utenti connessi: Nessun altro utente\n"
        self.main_display.update(self.main_display_text)

     elif msg.startswith("START;"):
        _, chat_id, peer = msg.split(";", 2)

        if chat_id not in self.chat_windows:
            chat = ChatWindow(chat_id, peer, self.sock)
            self.chat_windows[chat_id] = chat
            self.mount(chat)   

     elif msg.startswith("MSG;"):
        _, chat_id, sender, text = msg.split(";", 3)

        if chat_id not in self.chat_windows:
            chat = ChatWindow(chat_id, sender, self.sock)
            self.chat_windows[chat_id] = chat
            self.mount(chat)

        self.chat_windows[chat_id].receive_message(sender, text)

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
                    self.sock.sendall(f"CHAT {parts[1]}\n".encode())
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
