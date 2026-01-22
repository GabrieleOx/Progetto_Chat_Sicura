import socket
import threading

HOST = "localhost"
PORT = 3000

clientListConn = []
clientListAddr = []
lock = threading.Lock()

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)

    print("Server Attivo!")

    th = threading.Thread(target=accettaConnessioni, args=(sock,))
    th.start()

def printClientList(conn):
    with lock:
        msg = "messaggia con:\n"
        cont = 1
        for c, addr in zip(clientListConn, clientListAddr):
            if c is not conn:
                msg += f"{cont}) {addr}\n"
                cont += 1
    return msg.encode()


def mainSrvPart(conn):
    msg = printClientList(conn)
    conn.sendall(msg)

    data = conn.recv(1024)
    if not data:
        remove_client(conn)
        return

    try:
        scelta = int(data.decode().strip())
        if scelta < 1 or scelta > len(clientListConn):
            conn.sendall(b"Scelta non valida.\n")
            remove_client(conn)
            return
        connTo = clientListConn[scelta - 1]
    except ValueError:
        conn.sendall(b"Input non valido.\n")
        remove_client(conn)
        return
    
    thA = threading.Thread(target=recv_and_send, args=(conn, connTo))
    thB = threading.Thread(target=recv_and_send, args=(connTo, conn))

    thA.start()
    thB.start()

    thA.join()
    thB.join()


def recv_and_send(conn, connTo):
    while True:
        try:
            msg = conn.recv(8192)
            if not msg:
                print(f"{conn.getpeername()} ha chiuso")
                break
            connTo.sendall(msg)
        except Exception as e:
            print(f"Errore su {conn.getpeername()}: {e}")
            break
        
    remove_client(conn)


def accettaConnessioni(sock):
    while True:
        conn, addr = sock.accept()
        print("Connessione accettata:", addr)
        with lock:
            clientListConn.append(conn)
            clientListAddr.append(addr)
        th = threading.Thread(target=mainSrvPart, args=(conn,))
        th.start()


def remove_client(conn):
    with lock:
        if conn in clientListConn:
            index = clientListConn.index(conn)
            addr = clientListAddr[index]
            clientListConn.pop(index)
            clientListAddr.pop(index)
            print(f"Client rimosso: {addr}")
    try:
        conn.close()
    except:
        pass


if __name__ == "__main__":
    main()