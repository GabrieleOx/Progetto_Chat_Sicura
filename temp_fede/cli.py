import socket
import threading
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Vertical

HOST = "localhost"
PORT = 3000


class ChatApp(App):
    CSS = "Static { height: 1fr; }"

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
        self.chats = {}  # chat_id -> {peer, messages[]}

        self.render_menu()

        threading.Thread(target=self.listen, daemon=True).start()

    # ================= NETWORK =================

    def listen(self): #thread che riceve messaggi, li decodifica e splitta in una lista (protocollo con ;)
        buffer = ""
        while True:
            try:
                data = self.sock.recv(1024)
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
            _, chat_id, peer = msg.split(";", 2)
            if chat_id not in self.chats:
                self.chats[chat_id] = {
                    "peer": peer,
                    "messages": []
                }
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
       

        if text.startswith("CHAT "):
            _, uid = text.split(" ", 1)
            self.sock.sendall(f"CHAT;{uid}\n".encode())

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
            self.chats[chat_id]["messages"].append(
                f"[cyan]Tu: {text}[/]"
            )
            self.sock.sendall(f"MSG;{chat_id};{text}\n".encode())
            self.render_chat(chat_id)


if __name__ == "__main__":
    ChatApp().run()
