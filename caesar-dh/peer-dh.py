import socket
import asyncio
from input_utils import *
from sympy.ntheory import isprime
from random import randint
from aioconsole import ainput
#this uses diffie hellman for key exchange and cyphers text with caesar cypher

async def main():
    print("Definisci la porta su cui ascoltare l'altro peer")
    listen_at = (get_address(), get_port())
    print(
        f"Peer in attesa: per connetterti utilizza l'IP {listen_at[0]} e la porta {listen_at[1]}.")
    print("Definisci ora la connessione all'altro peer")
    send_to = (get_ip(), get_port())
    if listen_at == send_to:
        exit("no.")
    try:
        connection = Peer(listen_at)
        await asyncio.gather(connection.listen(), connection.connect(send_to))
        print("Connessione stabilita... Scambio la chiave...")
        await asyncio.gather(connection.exchange_key())
        print("Qualsiasi cosa scrivi da adesso arriverà all'altro peer..")
        await asyncio.gather(connection.prompt(), connection.wait())
    except:
        connection.end()
        exit("Connessione chiusa.")


class Peer:
    def __init__(self, listen_at: tuple):
        self._ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._ss.bind((listen_at))
        self._cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._conn = None
        self._key = None

    def _encrypt(self, data: str) -> str:
        new_str = ""
        for c in data:
            shifted = ord(c)+self._key
            new_str += c if not c.isalpha() else (chr((shifted)) if shifted <=
                                                  ord("Z" if c.isupper() else "z") else chr(shifted-26))
        return new_str

    def _decrypt(self, data: str) -> str:
        new_str = ""
        for c in data:
            shifted = ord(c)-self._key
            new_str += c if not c.isalpha() else (chr((shifted)) if shifted >=
                                                  ord("A" if c.isupper() else "a") else chr(shifted+26))
        return new_str

    def _safe_send(self, data: str):
        self._cs.send(self._encrypt(data).encode())
        assert self._cs.recv(1024).decode() == "recv"

    async def _safe_recv(self) -> str:
        while True:
            data = await asyncio.get_event_loop().sock_recv(self._conn, 1024)
            if data:
                data = self._decrypt(data.decode())
                self._conn.send("recv".encode())
                return data

    def _recv_key(self, timeout: float) -> bool or int:
        success = True
        try:
            self._conn.settimeout(timeout)
            val = int(self._conn.recv(1024))
            self._conn.send("recv".encode())
        except TimeoutError:
            success = False
        self._conn.settimeout(0)
        return success if not success else val

    def _send_key(self, prime: bool = False) -> int:
        val = randint(2**512, 2**1024) if prime else randint(2**0, (2**512)-1)
        while prime and not isprime(val):
            val = randint(2**512, 2**1024)
        self._cs.send(str(val).encode())
        assert self._cs.recv(1024).decode() == "recv"
        return val

    async def exchange_key(self):
        p = self._recv_key(randint(1, 50000000000)/10000000000)
        p = p if p else self._send_key(True)
        g = self._recv_key(randint(1, 10000000000)/10000000000)
        g = g if g else self._send_key()
        n = randint(2**512, 2**1024)
        self._cs.send(str(pow(g, n, p)).encode())
        self._key = (pow(int((await asyncio.get_event_loop().sock_recv(self._conn, 1024)).decode()), n, p) % 25) + 1

    async def listen(self):
        self._ss.listen()
        self._conn, addr = await asyncio.get_running_loop().run_in_executor(None, self._ss.accept)

    async def connect(self, send_to: tuple):
        while True:
            try:
                await asyncio.get_running_loop().run_in_executor(None, self._cs.connect, send_to)
            except:
                continue
            else:
                break

    async def prompt(self):
        while True:
            data = await ainput()
            self._safe_send(data)
            if data == "fine":
                self.end()

    async def wait(self):
        while True:
            data = await self._safe_recv()
            if data == "fine":
                self.end()
            else:
                print(f"Peer: {data}")

    def end(self):
        self._conn.close()
        self._ss.close()
        self._cs.close()


if __name__ == "__main__":
    asyncio.run(main())
