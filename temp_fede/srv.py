import socket
import threading
import uuid

HOST = "localhost"
PORT = 3000

clients = {}  # client_id -> conn
chats = {}    # chat_id -> {"participants": [client1, client2]}
lock = threading.Lock()

def safe_send(conn, msg):
    try:
        conn.sendall((msg + "\n").encode())
    except:
        print("hola")
        pass

def broadcast_users():
    """Invia lista utenti a tutti i client"""
    with lock:
        for cid, conn in clients.items():
            others = [c for c in clients if c != cid]
            msg = "USERS;" + (";".join(others) if others else "Nessun altro utente")
            safe_send(conn, msg)

def start_chat(sender_id, target_id):
    """Crea chat_id unico e informa entrambi i client"""
    with lock:
        if sender_id not in clients or target_id not in clients:
          
            return
        chat_id = str(uuid.uuid4())[:8]
        chats[chat_id] = {"participants": [sender_id, target_id]}
        print("ciao")
        safe_send(clients[sender_id], f"START;{chat_id};{target_id}")
        safe_send(clients[target_id], f"START;{chat_id};{sender_id}")

def relay_message(sender_id, chat_id, text):
    """Invia messaggio nella chat a tutti tranne il mittente"""
    with lock:
        if chat_id not in chats:
            return
        for p in chats[chat_id]["participants"]:
            if p != sender_id and p in clients:
                safe_send(clients[p], f"MSG {chat_id} {sender_id} {text}")

def close_chat(client_id, chat_id):
    """Chiude chat e notifica l’altro lato"""
    with lock:
        if chat_id not in chats:
            return
        participants = chats[chat_id]["participants"]
        for p in participants:
            if p != client_id and p in clients:
                safe_send(clients[p], f"CLOSE {chat_id}")
        del chats[chat_id]

def process_message(client_id, msg):
    if not msg:
        return
    parts = msg.split(" ", 2)
    cmd = parts[0].upper()

    if cmd == "LIST":
        broadcast_users()
    elif cmd == "CHAT" and len(parts) == 2:
        print("ciao")
        print(clients)
        print(parts[1])
        print(client_id)
        start_chat(client_id, parts[1])
    elif cmd == "MSG" and len(parts) == 3:
        chat_id, text = parts[1], parts[2]
        relay_message(client_id, chat_id, text)
    elif cmd == "CLOSE" and len(parts) == 2:
        chat_id = parts[1]
        close_chat(client_id, chat_id)

def handle_client(conn):
    client_id = str(uuid.uuid4())[:8]
    with lock:
        clients[client_id] = conn

    safe_send(conn, f"ID {client_id}")
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
    except:
        pass
    finally:
        with lock:
            if client_id in clients:
                del clients[client_id]
            # chiudi tutte le chat del client
            to_close = [chat_id for chat_id, info in chats.items() if client_id in info["participants"]]
            for chat_id in to_close:
                close_chat(client_id, chat_id)
        broadcast_users()
        conn.close()

def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server attivo su {HOST}:{PORT}")

    while True:
        conn, _ = s.accept()
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    main()
