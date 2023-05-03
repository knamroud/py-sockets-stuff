import socket


def get_address() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    IP = s.getsockname()[0]
    s.close()
    return IP


def get_ip() -> str:
    while True:
        try:
            ip = input("Inserisci l'indirizzo IP: ")
            assert False not in [int(octet) >= 0 and int(octet) <= 255
                                 for octet in ip.split(".")] + [ip.count(".") == 3]
        except:
            print("IP non valido!")
        else:
            return ip


def get_port() -> int:
    while True:
        try:
            assert (port := int(input("Inserisci la porta: "))
                    ) >= 1024 and port <= 65535
        except:
            print("Porta non valida!")
        else:
            return port
