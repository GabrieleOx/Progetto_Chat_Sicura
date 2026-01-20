import socket
import threading
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Static
from textual.containers import Vertical

HOST = "localhost"
PORT = 3000

class Chat(App):
    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            self.chat = Static()
            yield self.chat
            yield Input(placeholder="Scrivi...")
        yield Footer()

    def on_mount(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))
        threading.Thread(target=self._recv, daemon=True).start()

    def _recv(self):
        while True:
            try:
                msg = self.sock.recv(1024)
                if not msg:
                    break
                self.call_from_thread(self._add, msg.decode())
            except:
                break

    def _add(self, msg):
        self.chat.update(self.chat.renderable + msg + "\n")

    def on_input_submitted(self, event):
        try:
            self.sock.sendall(event.value.encode())
            event.input.value = ""
        except:
            self.exit()

    def on_shutdown_request(self):
        try:
            self.sock.close()
        except:
            pass
        self.exit()

if __name__ == "__main__":
    Chat().run()
