import socket
import sys
import threading

HOST = "127.0.0.1"
PORT = 3000

chat_id = sys.argv[1]
peer = sys.argv[2]

sock = socket.socket()
sock.connect((HOST, PORT))


def listen():
    while True:
        data = sock.recv(1024).decode().strip()
        if data.startswith("MSG;"):
            _, _, sender, text = data.split(";", 3)
            print(f"\n{sender}: {text}")
        elif data.startswith("CLOSE;"):
            print("Chat chiusa")
            exit()


threading.Thread(target=listen, daemon=True).start()

print(f"Chat con {peer} (scrivi /exit per uscire)")

while True:
    msg = input()
    if msg == "/exit":
        sock.sendall(f"CLOSE;{chat_id}\n".encode())
        break
    sock.sendall(f"MSG;{chat_id};{msg}\n".encode())
