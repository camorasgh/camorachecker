import json
import requests
import threading
import os
from rich.console import Console
from rich.text import Text
import time
from pathlib import Path
import random
import urllib3
urllib3.disable_warnings()

console = Console()
checked_count = 0
lock = threading.Lock()
proxy_index = 0

def gradient_print(text, start_color=(147, 51, 234), end_color=(59, 130, 246)):
    for line in text.split('\n'):
        gradient_text = Text(line)
        gradient_text.stylize(f"rgb({start_color[0]},{start_color[1]},{start_color[2]}) bold")
        console.print(gradient_text)

def print_banner():
    os.system('title Token Checker')
    banner = """
   ______                                    ________              __            
  / ____/___ _____ ___  ____  _________ _   / ____/ /_  ___  _____/ /_____  _____
 / /   / __ `/ __ `__ \/ __ \/ ___/ __ `/  / /   / __ \/ _ \/ ___/ //_/ _ \/ ___/
/ /___/ /_/ / / / / / / /_/ / /  / /_/ /  / /___/ / / /  __/ /__/ ,< /  __/ /    
\____/\__,_/_/ /_/ /_/\____/_/   \__,_/   \____/_/ /_/\___/\___/_/|_|\___/_/                                                                                                                                                                                                                                           
"""
    gradient_print(banner)

def setup_output_directory():
    Path("output").mkdir(exist_ok=True)
    open("output/valid.txt", "w").close()
    open("output/invalid.txt", "w").close()

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def load_tokens():
    with open(config["tokens_location"], "r") as f:
        return [line.strip().split(':')[-1] for line in f if line.strip()]

def load_proxies():
    if not config["use_proxies"]:
        return []
    with open(config["proxies_location"], "r") as f:
        return [line.strip() for line in f if line.strip()]

def truncate_token(token):
    return token[:25] + "..."

def save_token(token, status):
    filename = "output/valid.txt" if status == "valid" else "output/invalid.txt"
    with lock:
        with open(filename, "a") as f:
            f.write(f"{token}\n")

def check_token(token, proxy_pool):
    global checked_count, proxy_index
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    status = None
    for _ in range(5):
        try:
            with lock:
                if proxy_pool:
                    current_proxy = proxy_pool[proxy_index % len(proxy_pool)]
                    proxy_index += 1
                else:
                    current_proxy = None

            proxies = {"http": f"http://{current_proxy}", "https": f"http://{current_proxy}"} if current_proxy else None

            response = requests.get(
                "https://discord.com/api/v9/users/@me",
                headers=headers,
                proxies=proxies,
                timeout=15,
                verify=False
            )

            if response.status_code == 200:
                status = "valid"
                break
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 1)
                time.sleep(retry_after)
                continue
            else:
                status = "invalid"
                break

        except Exception as e:
            time.sleep(1)
            continue

    with lock:
        checked_count += 1
        if status == "valid":
            console.print(f"[bold green][VALID][/bold green] {truncate_token(token)}")
            save_token(token, "valid")
        else:
            console.print(f"[bold red][INVALID][/bold red] {truncate_token(token)}")
            save_token(token, "invalid")

def worker(tokens, proxy_pool):
    for token in tokens:
        check_token(token, proxy_pool)

def chunk_list(lst, n):
    return [lst[i::n] for i in range(n)]

def process_tokens(tokens, proxy_pool):
    num_threads = len(proxy_pool) if proxy_pool else 100
    chunks = chunk_list(tokens, num_threads)
    threads = []
    
    for chunk in chunks:
        thread = threading.Thread(target=worker, args=(chunk, proxy_pool))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    setup_output_directory()
    
    config = load_config()
    tokens = load_tokens()
    proxies = load_proxies()
    
    console.print(f"[bold rgb(147,51,234)][NOTIFICATION] Starting check with {len(proxies)} proxies[/bold rgb(147,51,234)]")
    console.print(f"[bold rgb(147,51,234)][NOTIFICATION] Processing {len(tokens)} tokens[/bold rgb(147,51,234)]")
    
    process_tokens(tokens, proxies)
    
    console.print(f"[bold rgb(147,51,234)][COMPLETE] Checked {checked_count} tokens[/bold rgb(147,51,234)]")