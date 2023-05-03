from os.path import exists
from os import mkdir
from sympy.ntheory import isprime
from random import randint
import base64
import multiprocessing

PROC_POOL = 3  # Processi avviati per la generazione di un singolo numero


def main():
    if not exists("./keys"):
        mkdir("./keys")
    keys = gen_keys(get_key_size())
    save_pem(keys["pub"], "./keys/pub.pem", "public")
    print(keys["pub"] == load_pem("./keys/pub.pem"))


def get_key_size() -> int:
    while True:
        try:
            assert (size := int(input(
                "Inserisci la dimensione della chiave (1024, 2048 o 4096): "))) in (1024, 2048, 4096)
        except:
            print("Dimensione della chiave non valida!")
        else:
            return size


def gen_prime(r: tuple[int, int], return_dict: dict, var: str) -> None:
    while not isprime((i := randint(r[0], r[1]))):
        continue
    return_dict[var] = i


def pool_gen_prime(r: tuple[int, int], return_dict: dict, var: str) -> None:
    jobs = [multiprocessing.Process(target=gen_prime, args=(
        r, return_dict, var)) for i in range(PROC_POOL)]
    for job in jobs:
        job.start()
    while not return_dict.get(var):
        continue
    for job in jobs:
        job.kill()


def get_p_q(size: int) -> tuple[int, int]:
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    jobs = []
    for c in "pq":
        shift = randint(2**2, 2**8)
        jobs.append(multiprocessing.Process(
            target=pool_gen_prime, args=((2**((size//2)-shift), 2**((size//2)+shift)), return_dict, c)))
        jobs[-1].start()
    for job in jobs:
        job.join()
    return return_dict["p"], return_dict["q"]


def get_e(r: tuple[int, int]) -> int:
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    flag = True
    while flag:
        job = multiprocessing.Process(
            target=pool_gen_prime, args=(r, return_dict, "e"))
        job.start()
        job.join()
        flag = r[1]+1 % return_dict["e"] == 0
    return return_dict["e"]


def gen_keys(size: int) -> dict[str: tuple[int, int]]:
    (p, q) = get_p_q(size)
    n = p*q
    phi = (p-1)*(q-1)
    e = get_e((2**(size//2), phi-1))
    d = pow(e, -1, phi)
    return {"pub": (n, e), "priv": (n, d)}


def save_pem(key: tuple[int, int], file: str, t: str) -> None:
    t = t.upper()
    assert t in ("PUBLIC", "PRIVATE")
    f = open(file, "wb+")
    contents = base64.standard_b64encode(
        (" - ".join(map(str, key))).encode()).replace(b"\n", b"")
    pem = b"\n".join([contents[start: start + 64]
                      for start in range(0, len(contents), 64)])
    pem = f"-----BEGIN RSA {t} KEY-----\n".encode() + \
        pem + f"\n-----END RSA {t} KEY-----".encode()
    f.write(pem)
    f.close()


def load_pem(file: str) -> tuple[int, int]:
    f = open(file, "rb")
    key = tuple(map(int, base64.standard_b64decode(
        b"".join(f.readlines()[1:-1])).decode().split(" - ")))
    f.close()
    return key


def encrypt(data: int, key: tuple[int, int]) -> int:
    return pow(data, key[1], key[0])


def decrypt(data: int, key: tuple[int, int]) -> int:
    return pow(data, key[1], key[0])


if __name__ == "__main__":
    main()
