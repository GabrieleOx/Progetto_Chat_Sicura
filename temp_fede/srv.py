import socket
import time
import threading

def main():
    HOST = "localhost"
    PORT = 3000

    clientListConn=[]
    clientListAddr=[]
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(5)

    print("Server Attivo!")
    
    thread = threading.Thread(target=accettaConnessioni, args=(sock, clientListConn, clientListAddr)) 
    thread.start()

   #sock.close()

def printClientList(clientList, conn, clientListAddr): #creo la lista di destinatari tra cui scegliere
    msg="messaggia con:\n"
    cont=1
    cont2=0
    for i in clientList:
        if i != conn:
            msg+=str(cont)+") "+str(clientListAddr[cont2])+"\n"
            cont+=1
        cont2
    return msg.encode()

def mainSrvPart(conn, clientList, clientListAddr):
    conn.sendall(printClientList(clientList, conn, clientListAddr))
    destinatario = conn.recv(1024).decode()
    connTo=clientList[int(destinatario)-1]
    conn.sendall("start".encode())
    connTo.sendall("start".encode())
    '''threadA = threading.Thread(target=recv_and_send, args=(conn, connTo)) 
    threadA.start()
    threadB = threading.Thread(target=recv_and_send, args=(connTo, conn)) 
    threadB.start()
    '''

    while True:
        time.sleep(100)
    conn.close()
    clientList.remove(conn)

def recv_and_send(conn, connTo):
    while True:
        msg=conn.recv(1024)
        connTo.sendall(msg)

def accettaConnessioni(sock, clientList, clientListAddr):
    while True:
        conn, addr = sock.accept()
        print("Connessione accettata: ", addr)
        clientListAddr.append(addr)
        clientList.append(conn)
        thread = threading.Thread(target=mainSrvPart, args=(conn, clientList, clientListAddr))
        thread.start()


if __name__=="__main__":
    main()