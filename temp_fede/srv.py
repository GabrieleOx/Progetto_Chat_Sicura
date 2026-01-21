import socket
import threading
import uuid



HOST = "localhost"
PORT = 3000

clients = {}   # client_id -> conn
chats = {}     # chat_id -> {"participants": [id1, id2]}
lock = threading.Lock()


def safe_send(conn, msg):
    try:
        conn.sendall((msg + "\n").encode())
    except:
        pass


def broadcast_users():

    
    with lock:
        for cid, conn in clients.items():
            others = [c for c in clients if c != cid]
            safe_send(conn, "USERS;" + ";".join(others))


def start_chat(sender_id, target_id):
    with lock:
        if sender_id not in clients or target_id not in clients:
            return

        chat_id = str(uuid.uuid4())[:8]
        chats[chat_id] = {"participants": [sender_id, target_id]}

        safe_send(clients[sender_id], f"START;{chat_id};{target_id}")
        safe_send(clients[target_id], f"START;{chat_id};{sender_id}")


def relay_message(sender_id, chat_id, text):
    with lock:
        if chat_id not in chats:
            return

        for p in chats[chat_id]["participants"]:
            if p != sender_id and p in clients:
                safe_send(clients[p], f"MSG;{chat_id};{sender_id};{text}")


def close_chat(client_id, chat_id):
    with lock:
        if chat_id not in chats:
            return

        for p in chats[chat_id]["participants"]:
            if p != client_id and p in clients:
                safe_send(clients[p], f"CLOSE;{chat_id}")

        del chats[chat_id]


def process_message(client_id, msg):
    if not msg:
        return

    # AL MASSIMO 2 split -> ottieni 3 parti
    parts = msg.split(";", 2)
    cmd = parts[0]

    if cmd == "LIST":
        broadcast_users()

    elif cmd == "CHAT" and len(parts) == 2:
        start_chat(client_id, parts[1])

    elif cmd == "MSG" and len(parts) == 3:
        chat_id = parts[1]
        text = parts[2]
        relay_message(client_id, chat_id, text)

    elif cmd == "CLOSE" and len(parts) == 2:
        close_chat(client_id, parts[1])


def handle_client(conn):
    client_id = str(uuid.uuid4())[:8]

    with lock:
        clients[client_id] = conn

    safe_send(conn, f"ID;{client_id}")
    broadcast_users()

    buffer = ""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            buffer += data.decode()
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                process_message(client_id, line.strip())
    finally:
        with lock:
            clients.pop(client_id, None)

        broadcast_users()
        conn.close()


def main():
    s = socket.socket()
    s.bind((HOST, PORT))
    s.listen()
    print("Server avviato")

    while True:
        conn, _ = s.accept()
        threading.Thread(
            target=handle_client,
            args=(conn,),
            daemon=True
        ).start()


if __name__ == "__main__":
    main()
