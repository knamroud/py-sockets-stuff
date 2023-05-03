import socket
import asyncio
from rsa import load_pem, encrypt, decrypt
from input_utils import *
from random import randint
from aioconsole import ainput
# this uses rsa to exchange the caesar key. use rsa.py to generate the key pair.

async def main():
    print("Definisci la porta su cui ascoltare l'altro peer")
    listen_at = (get_address(), get_port())
    print(
        f"Peer in attesa: per connetterti utilizza l'IP {listen_at[0]} e la porta {listen_at[1]}.")
    print("Definisci ora la connessione all'altro peer")
    send_to = (get_ip(), get_port())
    try:
        connection = Peer(listen_at)
        await asyncio.gather(connection.listen(), connection.connect(send_to))
        print("Connessione stabilita... Scambio la chiave...")
        connection.exchange_key()
        print("Qualsiasi cosa scrivi da adesso arriverà all'altro peer..")
        await asyncio.gather(connection.prompt(), connection.wait())
    except Exception as e:
        print(e)
        connection.end()
        print("Connessione chiusa.")
        exit()


class Peer:
    def __init__(self, listen_at: tuple):
        self._ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._ss.bind((listen_at))
        self._cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._conn = None
        self._key = None
        self._pub_key = load_pem("./keys/pub.pem")
        self._priv_key = load_pem("./keys/priv.pem")

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

    def _send_key(self):
        self._key = randint(1, 25)
        k = str(encrypt(self._key, self._pub_key)).encode()
        self._cs.send(k)
        assert self._cs.recv(1024).decode() == "recv"

    def _recv_key(self, timeout: float) -> bool:
        success = True
        try:
            self._conn.settimeout(timeout)
            self._key = decrypt(
                int(self._conn.recv(4096).decode()), self._priv_key)
            self._conn.send("recv".encode())
        except TimeoutError:
            success = False
        self._conn.settimeout(0)
        return success

    def exchange_key(self):
        if not self._recv_key(randint(10, 1000000)/1000000):
            self._send_key()
        print(self._key)

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
