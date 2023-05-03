import socket
from random import randint

MOVES = ["Sasso", "Carta", "Forbice"]


def main():
    s = socket.socket()
    connect(s)
    while True:
        try:
            safe_send(s, -1)
            move = randint(0, 2)
            print(f"Il client ha generato {MOVES[move]}, invio al server...")
            safe_send(s, move)
            smove = safe_recv(s)
            result = safe_recv(s)
            print(result)
            print(f"Il server ha giocato {MOVES[smove]}. Hai {'vinto' if result == 0 else 'perso' if result == 1 else 'pareggiato'}!")
            if input("Giocare ancora? y per rigiocare, qualsiasi altro valore per uscire: ").lower().strip() != "y":
                end_game(s)
                break
        except KeyboardInterrupt:
            print("CTRL+C rompe tutto...no....")


def connect(s: socket.socket):
    while True:
        try:
            s.settimeout(5)
            s.connect((get_ip(), get_port()))
            assert s.recv(1024).decode() == "on"
            s.settimeout(None)
        except:
            print("Connessione fallita. Verificare IP e porta inseriti.")
        else:
            break


def get_ip() -> str:
    while True:
        try:
            ip = input("Inserisci l'indirizzo IP: ")
            assert False not in [int(octet) in range(0, 256)
                                 for octet in ip.split(".")] + [ip.count(".") == 3]
        except:
            print("IP non valido;")
        else:
            return ip


def get_port() -> int:
    while True:
        try:
            assert (port := int(input("Inserisci la porta: "))
                    ) >= 1024 and port <= 65535
        except:
            print("Porta non valida;")
        else:
            return port


def safe_send(s: socket.socket, data: int):
    s.send(str(data).encode())
    assert int(s.recv(8).decode()) == -1


def safe_recv(s: socket.socket):
    data = int(s.recv(8).decode())
    s.send("-1".encode())
    return data


def end_game(s: socket.socket):
    safe_send(s, -2)
    risultati = (safe_recv(s), safe_recv(s), safe_recv(s))
    print(
        f"Riepilogo esiti\nGiochi totali: {sum(risultati)}\nVittorie: {risultati[0]}\nSconfitte: {risultati[1]}\nPareggi: {risultati[2]}")
    s.close()


if __name__ == "__main__":
    main()
