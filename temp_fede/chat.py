from textual.containers import Vertical
from textual.widgets import Static, Input
from colorama import Fore, Style, init

init(autoreset=True)

class ChatWindow(Vertical):

    from colorama import Fore, Style, init
init(autoreset=True)

class ChatWindow(Vertical):
    def __init__(self, chat_id, peer_id, sock):
        super().__init__()
        self.chat_id = chat_id
        self.peer_id = peer_id
        self.sock = sock
        self._chat_text = ""
        self._client_id = None
        self.input = None
        self.chat_log = None

        # Colori locali
        self.my_color = Fore.CYAN
        self.peer_color = Fore.GREEN

    def receive_message(self, sender_id, text, local=False):
        """Mostra messaggio nella chat. 
        local=True se è stato inviato da noi."""
        if local:
            display_name = "Tu"
            color = self.my_color
        else:
            if sender_id == self._client_id:
                display_name = "Tu"
                color = self.my_color
            else:
                display_name = sender_id
                color = self.peer_color

        self._chat_text += f"\n{color}{display_name}: {text}{Style.RESET_ALL}"
        self.chat_log.update(self._chat_text)

    def on_input_submitted(self, event):
        event.stop()
        text = event.value.strip()
        event.input.value = ""

        if text:
            # Mostra subito nella chat (locale)
            self.receive_message(self._client_id, text, local=True)

            # Invia al server
            self.sock.sendall(f"MSG;{self.chat_id};{text}\n".encode())

    def compose(self):
        yield Static(f"Chat con {self.peer_id}")
        self.chat_log = Static("")
        yield self.chat_log
        self.input = Input(placeholder="Messaggio...")
        yield self.input

    def on_mount(self):
        # Forza focus sull'input della chat
        self.set_timer(0, self.force_focus)

    def force_focus(self):
        self.input.can_focus = True
        self.input.focus()

    

    

    def on_key(self, event):
        '''if event.key == "escape":
            self.app.main_input.can_focus = True
            self.app.main_input.focus()'''
