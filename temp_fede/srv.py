# server.py
import socket
import threading

HOST = "localhost"
PORT = 3000

clientListConn = []
clientListAddr = []

def printClientList(conn):
    msg = "Messaggia con:\n"
    cont = 1
    for c in clientListConn:
        if c != conn:
            idx = clientListConn.index(c)
            msg += f"{cont}) {clientListAddr[idx]}\n"
            cont += 1
    return msg.encode()

def relay(src, dst):
    while True:
        try:
            msg = src.recv(1024)
            if not msg:
                break
            dst.sendall(msg)
        except:
            break

def handleClient(conn):
    
        # FASE 1: scelta destinatario
        conn.sendall(printClientList(conn))
        destinatario = conn.recv(1024).decode()
        print(destinatario)
        try:
            idx = int(destinatario) - 1
        except ValueError:
            conn.sendall(b"Input non valido")
            conn.close()
            return

        if idx < 0 or idx >= len(clientListConn):
            conn.sendall(b"Destinatario non valido")
            conn.close()
            return

        connTo = clientListConn[idx]

        # FASE 2: chat
        conn.sendall(b"start")
        connTo.sendall(b"start")

        # Bidirezionale: due thread
        t1 = threading.Thread(target=relay, args=(conn, connTo))
        t2 = threading.Thread(target=relay, args=(connTo, conn))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    
        if conn in clientListConn:
            clientListConn.remove(conn)
        if conn in clientListAddr:
            clientListAddr.remove(conn)
        conn.close()
        print("Connessione chiusa")

def acceptConnections(sock):
    while True:
        conn, addr = sock.accept()
        clientListConn.append(conn)
        clientListAddr.append(addr)
        print("Connessione accettata:", addr)
        threading.Thread(target=handleClient, args=(conn,), daemon=True).start()

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)
    print("Server attivo su", HOST, PORT)
    acceptConnections(sock)

if __name__ == "__main__":
    main()
