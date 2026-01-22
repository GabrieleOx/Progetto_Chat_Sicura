import socket
import threading
import uuid

HOST = "127.0.0.1"
PORT = 3000

clients = {}   # id -> conn
chats = {}     # chat_id -> (id1, id2)
lock = threading.Lock()


def send(conn, msg):
    try:
        conn.sendall((msg + "\n").encode())
    except:
        pass


def broadcast_users():
    with lock:
        for cid, conn in clients.items():
            others = [x for x in clients if x != cid]
            send(conn, "USERS;" + ";".join(others))


def start_chat(a, b,sessionKey):
    with lock:
        if a not in clients or b not in clients:
            return

        chat_id = str(uuid.uuid4())[:8]
        chats[chat_id] = (a, b)
        

        send(clients[a], f"START;{chat_id};{b};{sessionKey}")
        send(clients[b], f"START;{chat_id};{a};{sessionKey}")


def relay(chat_id, sender, text):
    with lock:
        if chat_id not in chats:
            return
        a, b = chats[chat_id]
        target = b if sender == a else a
        if target in clients:
            send(clients[target], f"MSG;{chat_id};{sender};{text}")


def close_chat(chat_id):
    with lock:
        if chat_id not in chats:
            return
        a, b = chats.pop(chat_id)
        if a in clients:
            send(clients[a], f"CLOSE;{chat_id}")
        if b in clients:
            send(clients[b], f"CLOSE;{chat_id}")


def handle(conn):
    cid = str(uuid.uuid4())[:8]
    with lock:
        clients[cid] = conn

    send(conn, f"ID;{cid}")
    broadcast_users()

    buf = ""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buf += data.decode()
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                parts = line.split(";", 3)

                print(parts)

                if parts[0] == "CHAT":
                    start_chat(cid, parts[1],parts[2])

                elif parts[0] == "MSG":
                    relay(parts[1], cid, parts[2])

                elif parts[0] == "CLOSE":
                    close_chat(parts[1])
    finally:
        with lock:
            clients.pop(cid, None)
        broadcast_users()
        conn.close()


def main():
    s = socket.socket()
    s.bind((HOST, PORT))
    s.listen()
    print("Server avviato")

    while True:
        conn, _ = s.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
