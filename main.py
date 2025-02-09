import json
import requests
import threading
import os
from rich.console import Console
from rich.text import Text
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import urllib3
urllib3.disable_warnings()

console = Console()
checked_count = 0
lock = threading.Lock()

def gradient_print(text):
    gradient_text = Text(text)
    gradient_text.stylize("rgb(147,51,234) bold")
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

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def load_tokens(location):
    with open(location, "r") as f:
        return [line.strip().split(':')[-1] for line in f if line.strip()]

def load_proxies(location):
    with open(location, "r") as f:
        return [line.strip() for line in f if line.strip()]

def save_result(token, valid, config):
    filename = config["valid_output_location"] if valid else config["invalid_output_location"]
    with lock:
        with open(filename, "a") as f:
            f.write(f"{token}\n")

def check_token(args):
    global checked_count
    token, proxy, config = args
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    proxies = {
        "http": proxy,
        "https": proxy
    }
    
    try:
        response = requests.get(
            "https://discord.com/api/v9/users/@me",
            headers=headers,
            proxies=proxies,
            timeout=10,
            verify=False
        )
        
        with lock:
            checked_count += 1
        
        if response.status_code == 200:
            console.print(f"[bold green][VALID][/bold green] {token[:25]}...")
            save_result(token, True, config)
            return True
        else:
            console.print(f"[bold red][INVALID][/bold red] {token[:25]}...")
            save_result(token, False, config)
            return False
            
    except Exception:
        with lock:
            checked_count += 1
        console.print(f"[bold red][INVALID][/bold red] {token[:25]}...")
        save_result(token, False, config)
        return False

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner()
    
    config = load_config()
    
    Path("output").mkdir(exist_ok=True)
    open(config["valid_output_location"], "w").close()
    open(config["invalid_output_location"], "w").close()
    
    tokens = load_tokens(config["tokens_location"])
    proxies = load_proxies(config["proxies_location"]) if config["use_proxies"] else [""]
    
    console.print(f"[bold rgb(147,51,234)][NOTIFICATION] Starting check with {len(proxies)} proxies[/bold rgb(147,51,234)]")
    console.print(f"[bold rgb(147,51,234)][NOTIFICATION] Processing {len(tokens)} tokens[/bold rgb(147,51,234)]")
    
    check_pairs = []
    for i, token in enumerate(tokens):
        proxy = proxies[i % len(proxies)]
        check_pairs.append((token, proxy, config))
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        executor.map(check_token, check_pairs)
    
    console.print(f"[bold rgb(147,51,234)][COMPLETE] Checked {checked_count} tokens[/bold rgb(147,51,234)]")

if __name__ == "__main__":
    main()