import json
import requests
import threading
import os
from rich.console import Console
from rich.text import Text
from datetime import datetime
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
    os.system('title Enhanced Token Checker')
    banner = """
   ______      __        _ __          __   ________              __            
  / ____/_  __/ /_____ _(_) /__  ____/ /  / ____/ /_  ___  _____/ /_____  _____
 / /   / / / / __/ __ `/ / / _ \/ __  /  / /   / __ \/ _ \/ ___/ //_/ _ \/ ___/
/ /___/ /_/ / /_/ /_/ / / /  __/ /_/ /  / /___/ / / /  __/ /__/ ,< /  __/ /    
\____/\__,_/\__/\__,_/_/_/\___/\__,_/   \____/_/ /_/\___/\___/_/|_|\___/_/     
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

def save_result(token, details, valid, config):
    filename = config["valid_output_location"] if valid else config["invalid_output_location"]
    with lock:
        with open(filename, "a") as f:
            if valid:
                f.write(f"{token} | {details}\n")
            else:
                f.write(f"{token}\n")

def get_verification_status(user_data):
    flags = user_data.get("flags", 0)
    phone_verified = user_data.get("phone", False)
    email_verified = user_data.get("verified", False)
    
    statuses = []
    
    if phone_verified and email_verified:
        statuses.append("FV")
    elif phone_verified:
        statuses.append("PV")
    elif email_verified:
        statuses.append("EV")
    else:
        statuses.append("NV")
        
    if flags & 1 << 14:
        statuses.append("flagged")
    if flags & 1 << 13:
        statuses.append("locked")
        
    return statuses

def get_nitro_info(token, headers, proxies):
    try:
        response = requests.get(
            "https://discord.com/api/v9/users/@me/billing/subscriptions",
            headers=headers,
            proxies=proxies,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200 and response.json():
            nitro_data = response.json()[0]
            ends_at = nitro_data.get("current_period_end")
            if ends_at:
                expiry_date = datetime.fromtimestamp(ends_at).strftime("%Y-%m-%d")
                return f"Expiry:{expiry_date}"
        return ""
    except:
        return ""

def get_boost_info(token, headers, proxies):
    try:
        response = requests.get(
            "https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots",
            headers=headers,
            proxies=proxies,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            slots = response.json()
            total_boosts = len(slots)
            unused_boosts = sum(1 for slot in slots if not slot.get("premium_guild_id"))
            if total_boosts > 0:
                return f"Boosts:{unused_boosts}/{total_boosts}"
        return ""
    except:
        return ""

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
            user_data = response.json()
            verification_statuses = get_verification_status(user_data)
            nitro_info = get_nitro_info(token, headers, proxies)
            boost_info = get_boost_info(token, headers, proxies)
            
            output_parts = []
            if boost_info:
                output_parts.append(boost_info)
            if nitro_info:
                output_parts.append(nitro_info)
            
            status_parts = []
            for status in verification_statuses:
                if status in ["EV", "PV", "FV", "NV"]:
                    status_parts.append(f"type:[green]{status}[/green]")
                else:
                    status_parts.append(status)
            
            output_parts.extend(status_parts)
            details = " | ".join(output_parts)
            
            console.print(f"[green][VALID][/green] {token[:25]}... | {details}")
            save_result(token, details.replace("[green]", "").replace("[/green]", ""), True, config)
            return True
        else:
            console.print(f"[red][INVALID][/red] {token[:25]}...")
            save_result(token, "", False, config)
            return False
            
    except Exception as e:
        with lock:
            checked_count += 1
        console.print(f"[red][INVALID][/red] {token[:25]}...")
        save_result(token, "", False, config)
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