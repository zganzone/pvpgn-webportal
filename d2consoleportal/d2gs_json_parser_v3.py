import telnetlib
import re
import json
import os
from datetime import datetime

# --- КОНФИГУРАЦИЯ ---
HOST = "192.168.88.41"
PORT = 8888
PASSWORD = "abcd123"
WEB_DATA_DIR = "/var/www/html/data/" # Дефинираме пътя към директорията

# --- Помощни функции за безопасно парсване (Остават същите) ---
def get_int_value(pattern, text, default=0):
# ... (Останалата част от get_int_value) ...
    match = re.search(pattern, text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return default
    return default

def get_float_value(pattern, text, default=0.0):
# ... (Останалата част от get_float_value) ...
    match = re.search(pattern, text)
    if match:
        try:
            value = match.group(1).replace('%', '').strip()
            return float(value)
        except ValueError:
            return default
    return default

def parse_memory_usage(pattern, text):
# ... (Останалата част от parse_memory_usage) ...
    line_match = re.search(pattern, text)
    if line_match:
        line = line_match.group(1)
        match = re.search(r"(\d+\.\d+)MB/\s*(\d+\.\d+)MB", line)
        if match:
            try:
                return {
                    "used_mb": float(match.group(1)),
                    "total_mb": float(match.group(2)),
                }
            except ValueError:
                pass 
    return {"used_mb": 0.0, "total_mb": 0.0}

# --- Основна функция за парсване (Променена за по-чист Uptime) ---
def parse_server_status_to_json():
    # ... (Част за свързване и изпълнение на Telnet - остава същата) ...
    results = {
        "status": "error",
        "message": "",
        "data": {}
    }
    
    uptime_raw = ""
    status_raw = ""

    try:
        tn = telnetlib.Telnet(HOST, PORT, timeout=5) 
        tn.read_until(b"pass:", timeout=2) 
        tn.write(PASSWORD.encode('ascii') + b"\n")
        tn.write(b"uptime\n")
        uptime_raw = tn.read_until(b"D2GS>", timeout=3).decode('ascii')
        tn.write(b"status\n")
        status_raw = tn.read_until(b"D2GS>", timeout=4).decode('ascii') 
        tn.close()
        
        if not status_raw or not uptime_raw:
             results["message"] = "Partial or no response received from server."
             return json.dumps(results, indent=4)
        
        results["status"] = "success"
        
    except Exception as e:
        results["message"] = f"Error connecting or executing command: {e}"
        return json.dumps(results, indent=4)

    # --- Uptime Parsing (Модифициран за чиста стойност) ---
    uptime_data = {}
    
    server_started_match = re.search(r"The game server started at (.*)", uptime_raw)
    uptime_duration_match = re.search(r"uptime (.*)", uptime_raw)
    current_time_match = re.search(r"Now it is (.*)", uptime_raw)

    if uptime_duration_match:
        # Извличаме само стойността на продължителността: "1 days 1 hours 5 minutes 32 seconds"
        duration_value = uptime_duration_match.group(1).strip()
        uptime_data["uptime_duration_value"] = duration_value
        
        # Записваме тази чиста стойност във файл, преди да продължим с JSON-а
        save_uptime_to_txt(duration_value)
        
        # ... (Калкулации за total_seconds и останалите uptime полета - остават същите) ...
        uptime_data["uptime_duration"] = duration_value
        
        parts = duration_value.split()
        try:
            days = int(parts[0])
            hours = int(parts[2])
            minutes = int(parts[4])
            seconds = int(parts[6])
            total_seconds = seconds + (minutes * 60) + (hours * 3600) + (days * 86400)
            uptime_data["uptime_total_seconds"] = total_seconds
        except (IndexError, ValueError):
            uptime_data["uptime_total_seconds"] = 0
            
    # ... (Останалата част от JSON парсването - остава същата) ...
    if server_started_match:
        uptime_data["server_start_time"] = server_started_match.group(1).strip()
    if current_time_match:
         uptime_data["current_time"] = current_time_match.group(1).strip()
         
    results["data"]["uptime"] = uptime_data
    # ... (Останалата част от status_data - остава същата) ...
    # ... (Всички останали парсвания на status_data, resource_usage, network_statistics - остават същите) ...
    # ... (Връщане на json.dumps(results, indent=4)) ...
    
    status_data = {} # (Трябва да съдържа всички други парснати данни)
    # ... (status_data парсинг) ...
    results["data"]["status"] = status_data # (Добавяме го тук)

    return json.dumps(results, indent=4)


# --- НОВА ФУНКЦИЯ ЗА TXT ЗАПИС ---

def save_uptime_to_txt(uptime_string):
    """Saves the plain uptime string to a text file for quick access."""
    file_path = os.path.join(WEB_DATA_DIR, "d2gs_uptime.txt")
    
    try:
        os.makedirs(WEB_DATA_DIR, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(uptime_string)
        # print(f"Успешен запис на Uptime в TXT: {file_path}")
    except OSError as e:
        print(f"Грешка при запис във TXT файл ({file_path}): {e}")
        print("Проверете правата за запис!")


# --- Актуализирано изпълнение на скрипта (if __name__ == "__main__":) ---
# ... (save_json_output остава същата, но използва новия WEB_DATA_DIR) ...
def save_json_output(json_data, directories, base_filename="d2gs_status"):
# ... (Останалата част на save_json_output) ...
# ...
    pass # Използвайте цялата save_json_output функция от предишния отговор

if __name__ == "__main__":
    json_output = parse_server_status_to_json()
    
    # Пътищата остават същите, просто използваме WEB_DATA_DIR
    output_directories = [
        WEB_DATA_DIR, 
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    ]
    
    save_json_output(json_output, output_directories)
    # (Можете да премахнете print(json_output) ако не Ви трябва дебъгване в конзолата)
