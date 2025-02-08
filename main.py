import json
import requests
import threading
from queue import Queue
import os
from rich.console import Console
from rich.text import Text
from rich import print as rprint
import time

console = Console()
checked_count = 0
lock = threading.Lock()

def gradient_print(text, start_color=(147, 51, 234), end_color=(59, 130, 246)):
    for line in text.split('\n'):
        gradient_text = Text(line)
        gradient_text.stylize(f"rgb({start_color[0]},{start_color[1]},{start_color[2]}) bold")
        console.print(gradient_text)

def print_banner():
    os.system('title Camora Checker I discord.gg/camora')
    banner = """
   ______                                    ________              __            
  / ____/___ _____ ___  ____  _________ _   / ____/ /_  ___  _____/ /_____  _____
 / /   / __ `/ __ `__ \/ __ \/ ___/ __ `/  / /   / __ \/ _ \/ ___/ //_/ _ \/ ___/
/ /___/ /_/ / / / / / / /_/ / /  / /_/ /  / /___/ / / /  __/ /__/ ,< /  __/ /    
\____/\__,_/_/ /_/ /_/\____/_/   \__,_/   \____/_/ /_/\___/\___/_/|_|\___/_/                                                                                                                                                                                                                                           
"""
    gradient_print(banner)

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

def check_token(token, proxy=None):
    global checked_count
    headers = {"Authorization": token, "Content-Type": "application/json"}
    proxies = {"http": proxy, "https": proxy} if proxy else None
    
    try:
        response = requests.get("https://discord.com/api/v9/users/@me", headers=headers, proxies=proxies, timeout=5)
        with lock:
            checked_count += 1
        
        if response.status_code == 200:
            rprint(f"[bold green][VALID][/bold green] {truncate_token(token)}")
        elif response.status_code == 429:
            reset_after = response.json().get('retry_after', 1)
            time.sleep(reset_after)
            return check_token(token, proxy)
        elif response.text.strip() == "":
            rprint(f"[bold yellow][ERROR][/bold yellow] {truncate_token(token)} - Empty response, retrying...")
            time.sleep(2)
            return check_token(token, proxy)
        else:
            rprint(f"[bold red][INVALID][/bold red] {truncate_token(token)}")
    except requests.exceptions.RequestException as e:
        rprint(f"[bold yellow][ERROR][/bold yellow] {truncate_token(token)} - Connection error: {e}")
    except json.JSONDecodeError:
        rprint(f"[bold yellow][ERROR][/bold yellow] {truncate_token(token)} - Invalid JSON response")
    except Exception as e:
        rprint(f"[bold yellow][ERROR][/bold yellow] {truncate_token(token)} - {str(e)}")

def worker():
    while True:
        try:
            token = queue.get(timeout=3)
        except:
            break
        proxy = proxies[checked_count % len(proxies)] if proxies else None
        check_token(token, proxy)
        queue.task_done()

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    config = load_config()
    tokens = load_tokens()
    proxies = load_proxies()
    queue = Queue()
    rprint(f"[bold rgb(147,51,234)][NOTIFICATION] Starting Checking {len(tokens)} Tokens[/bold rgb(147,51,234)]")
    for token in tokens:
        queue.put(token)
    threads = [threading.Thread(target=worker, daemon=True) for _ in range(min(50, len(tokens)))]
    for thread in threads:
        thread.start()
    queue.join()