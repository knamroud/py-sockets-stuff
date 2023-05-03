from threading import Thread
from random import randint
import socket
'''
sasso 0
carta 1
forbice 2
gioca ancora -1
fine gioco -2
(dal punto di vista del server)
sasso - carta = -1
sasso - forbice = -2
carta - sasso = 1
carta - forbice = -1
forbice - sasso = 2
forbice - carta = 1

quindi, server vince se ris = -2 o 1
client vince se ris = -1 o 2
pareggio se ris = 0
'''

def main():
    PORT = 6420
    clients = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        IP = s.getsockname()[0]
        s.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((IP, PORT))
        print(f"Server attivo: per connetterti dal client utilizza l'IP {IP} e la porta {PORT}")
        s.listen()
        while True:
            conn, addr = s.accept()
            conn.send("on".encode())
            clients.append(ConnectionThread(conn, addr))
            clients[-1].start()
    except KeyboardInterrupt:
        for client in clients:
            client.join()
        s.close()


class ConnectionThread(Thread):
    def __init__(self, conn, addr):
        Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.results = [0, 0, 0]

    def safe_send(self, data: int):
        self.conn.send(str(data).encode())
        assert int(self.conn.recv(8).decode()) == -1

    def safe_recv(self):
        data = int(self.conn.recv(8).decode())
        self.conn.send("-1".encode())
        return data

    def run(self):
        while self.safe_recv() == -1:
            print(f"Avviato giuoco con {self.addr}...\nAttendo la mossa del fra")
            cmove = self.safe_recv()
            move = randint(0, 2)
            result = move - cmove
            result = 0 if result in (-1, 2) else 1 if result in (-2, 1) else 2
            print(result)
            print(f"{'Azz io, server, ho perso' if result == 0 else 'Ho vinto :)' if result == 1 else 'Pareggio'}... Invio il risultato al fra...")
            self.safe_send(move)
            self.safe_send(result)
            self.results[result] += 1
        for r in self.results:
            self.safe_send(r)
        self.conn.close()

if __name__ == "__main__":
    main()
