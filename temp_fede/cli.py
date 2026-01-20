import socket
import subprocess
import sys

HOST = "localhost"
PORT = 3000

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    lista = sock.recv(2048).decode()
    print(lista)

    scelta = input("Scegli destinatario (numero): ")
    sock.sendall(scelta.encode())

    while True:
        msg = sock.recv(1024).decode()
        if msg == "start":
            sock.close()
            subprocess.Popen(
                [sys.executable, "chat.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            break

if __name__ == "__main__":
    main()
