from textual.containers import Vertical
from textual.widgets import Static, Input

class ChatWindow(Vertical):

    def __init__(self, chat_id, peer, sock):
        super().__init__()
        self.chat_id = chat_id
        self.peer = peer
        self.sock = sock

    def compose(self):
        yield Static(f"Chat con {self.peer}")
        self.chat_log = Static("")
        yield self.chat_log
        self.input = Input(placeholder="Messaggio...")
        yield self.input

    def on_mount(self):
        
        self.set_timer(0, self.force_focus)

    def force_focus(self):
        self.input.can_focus = True
        self.input.focus()

    def receive_message(self, sender, text):
        self.chat_log.update(
            self.chat_log.renderable + f"\n{sender}: {text}"
        )

    def on_input_submitted(self, event):
        text = event.value.strip()
        event.input.value = ""
        if text:
            self.sock.sendall(
                f"MSG;{self.chat_id};{text}\n".encode()
            )

    def on_key(self, event):
      
        if event.key == "escape":
            self.app.main_input.can_focus = True
            self.app.main_input.focus()
