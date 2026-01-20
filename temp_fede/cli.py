import socket
import threading
from multiprocessing import Process
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Vertical

# Finestra chat
class Connessione(App):
    def __init__(self, conn, nome_destinatario):
        super().__init__()
        self.conn = conn
        self.nome_destinatario = nome_destinatario
        self.chat_text = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            self.chat = Static(id="chat")
            yield self.chat
            yield Input(placeholder="Scrivi un messaggio...")
        yield Footer()

    def on_mount(self):
        threading.Thread(target=self.ricevi, daemon=True).start()

    def ricevi(self):
        while True:
            try:
                msg = self.conn.recv(1024).decode()
                if msg:
                    self.call_from_thread(self.update_chat, f"{self.nome_destinatario}: {msg}")
            except:
                break

    def update_chat(self, msg: str):
        self.chat_text += msg + "\n"
        self.chat.update(self.chat_text)

    def on_input_submitted(self, event: Input.Submitted):
        msg = event.value
        self.conn.sendall(msg.encode())
        self.update_chat(f"🟢 Tu: {msg}")
        event.input.value = ""


# Thread per terminale di scelta
def terminale_scelta(sock):
    while True:
        try:
            scelta = input("Scegli destinatario (numero) o invio per aggiornare lista: ")
            if scelta:
                sock.sendall(scelta.encode())
        except:
            break

# Funzione per aprire la chat in un processo separato
def apri_chat(sock, nome_destinatario):
    Connessione(sock, nome_destinatario).run()

def main():
    HOST = "localhost"
    PORT = 3000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    # Mostra lista client
    lista = sock.recv(1024).decode()
    print(lista)

    # Thread separato per terminale di scelta
    threading.Thread(target=terminale_scelta, args=(sock,), daemon=True).start()

    # Attesa "start" dal server
    while True:
        msg = sock.recv(1024).decode()
        if msg == "start":
            print("Chat avviata!")
            # Lancia la chat in un PROCESSO separato
            p = Process(target=apri_chat, args=(sock, "Destinatario"))
            p.start()
            break

    # Il terminale rimane libero per scegliere altre chat
    while True:
        pass

if __name__ == "__main__":
    main()
