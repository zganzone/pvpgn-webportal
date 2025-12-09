import telnetlib
import re
import json
from datetime import datetime, timedelta

HOST = "192.168.88.41"
PORT = 8888
PASSWORD = "abcd123"

# --- Помощни функции за безопасно парсване ---

def get_int_value(pattern, text, default=0):
    """Safely searches for a pattern and returns an integer value, 
    or a default value if not found."""
    match = re.search(pattern, text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return default
    return default

def get_float_value(pattern, text, default=0.0):
    """Safely searches for a pattern and returns a float value, 
    or a default value if not found."""
    match = re.search(pattern, text)
    if match:
        try:
            # Handle percentage case
            value = match.group(1).replace('%', '').strip()
            return float(value)
        except ValueError:
            return default
    return default

def parse_memory_usage(pattern, text):
    """Safely parses memory usage line (e.g., '0.000MB/ 0.000MB')."""
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
                pass # Return default if conversion fails
    return {"used_mb": 0.0, "total_mb": 0.0}

# --- Основна функция ---

def parse_server_status_to_json():
    """Connects to the D2GS server, executes 'uptime' and 'status', 
    and returns the parsed data as a JSON string."""
    
    # Initialize the results dictionary
    results = {
        "status": "error",
        "message": "",
        "data": {}
    }
    
    uptime_raw = ""
    status_raw = ""

    try:
        # Increase timeout slightly for better stability
        tn = telnetlib.Telnet(HOST, PORT, timeout=5) 
        
        # 1. Login (Sending the password)
        tn.read_until(b"pass:", timeout=2) 
        tn.write(PASSWORD.encode('ascii') + b"\n")
        
        # 2. Execute 'uptime'
        tn.write(b"uptime\n")
        uptime_raw = tn.read_until(b"D2GS>", timeout=3).decode('ascii')
        
        # 3. Execute 'status'
        tn.write(b"status\n")
        # Longer timeout for the status command as it has more output
        status_raw = tn.read_until(b"D2GS>", timeout=4).decode('ascii') 
        
        tn.close()
        
        if not status_raw or not uptime_raw:
             results["message"] = "Partial or no response received from server."
             return json.dumps(results, indent=4)
        
        results["status"] = "success"
        
    except Exception as e:
        results["message"] = f"Error connecting or executing command: {e}"
        return json.dumps(results, indent=4)

    # --- Uptime Parsing ---
    uptime_data = {}
    
    server_started_match = re.search(r"The game server started at (.*)", uptime_raw)
    uptime_duration_match = re.search(r"uptime (.*)", uptime_raw)
    current_time_match = re.search(r"Now it is (.*)", uptime_raw)

    if server_started_match:
        uptime_data["server_start_time"] = server_started_match.group(1).strip()
    if uptime_duration_match:
        duration_str = uptime_duration_match.group(1).strip()
        uptime_data["uptime_duration"] = duration_str
        
        # Calculate total seconds
        parts = duration_str.split()
        try:
            days = int(parts[0])
            hours = int(parts[2])
            minutes = int(parts[4])
            seconds = int(parts[6])
            total_seconds = seconds + (minutes * 60) + (hours * 3600) + (days * 86400)
            uptime_data["uptime_total_seconds"] = total_seconds
        except (IndexError, ValueError):
            uptime_data["uptime_total_seconds"] = 0
        
    if current_time_match:
         uptime_data["current_time"] = current_time_match.group(1).strip()

    results["data"]["uptime"] = uptime_data

    # --- Status Parsing: Game/User Stats ---
    status_data = {}
    
    status_data["game_limits"] = {
        # Using the safe helper functions
        "max_games_set": get_int_value(r"Setting maximum game:\s*(\d+)", status_raw),
        "max_games_current": get_int_value(r"Current maximum game:\s*(\d+)", status_raw),
        "max_prefer_users": get_int_value(r"Maximum prefer users:\s*(\d+)", status_raw),
        "max_game_life_seconds": get_int_value(r"Maximum game life:\s*(\d+)", status_raw),
    }
    
    status_data["current_activity"] = {
        "running_games": get_int_value(r"Current running game:\s*(\d+)", status_raw),
        "users_in_game": get_int_value(r"Current users in game:\s*(\d+)", status_raw),
    }
    
    # Connection status requires a match group 
    d2cs_match = re.search(r"Connetion to D2CS\s*(.*)", status_raw)
    d2dbs_match = re.search(r"Connetion to D2DBS\s*(.*)", status_raw)
    
    status_data["service_connections"] = {
        "d2cs": d2cs_match.group(1).strip() if d2cs_match else "Status Unknown",
        "d2dbs": d2dbs_match.group(1).strip() if d2dbs_match else "Status Unknown",
    }
    
    # --- Status Parsing: Resources (CPU/Memory) ---
    
    status_data["resource_usage"] = {
        "physical_memory": parse_memory_usage(r"Physical memory usage:\s*([^\n]+)", status_raw),
        "virtual_memory": parse_memory_usage(r"Virtual memory usage:\s*([^\n]+)", status_raw),
        "kernel_cpu_percent": get_float_value(r"Kernel CPU usage:\s*(\d+\.\d+)%", status_raw),
        "user_cpu_percent": get_float_value(r"User CPU usage:\s*(\d+\.\d+)%", status_raw),
    }

    # --- Status Parsing: Network Stats ---
    net_stats = {}
    
    # General Packets/Bytes section
    pkts_bytes_match = re.search(r"RecvPkts\s*RecvBytes\s*SendPkts\s*SendBytes([\s\S]*?)RecvRate", status_raw)
    if pkts_bytes_match:
        lines = pkts_bytes_match.group(1).strip().split('\n')
        net_stats["total_transfer"] = {}
        for line in lines:
            parts = line.split()
            # Check for exactly 5 parts (Service + 4 numbers)
            if len(parts) == 5 and parts[0] in ['D2CS', 'D2DBS']:
                service = parts[0]
                try:
                    net_stats["total_transfer"][service.lower()] = {
                        "recv_pkts": int(parts[1]),
                        "recv_bytes": int(parts[2]),
                        "send_pkts": int(parts[3]),
                        "send_bytes": int(parts[4]),
                    }
                except ValueError:
                    continue # Skip line if conversion fails

    # Rate section
    rates_match = re.search(r"RecvRate\s*PeakRecvRate\s*SendRate\s*PeakSendRate([\s\S]*)$", status_raw, re.MULTILINE)
    if rates_match:
        lines = rates_match.group(1).strip().split('\n')
        net_stats["rates_kbytes_sec"] = {}
        for line in lines:
            parts = line.split()
            if len(parts) == 5 and parts[0] in ['D2CS', 'D2DBS']:
                service = parts[0]
                try:
                    net_stats["rates_kbytes_sec"][service.lower()] = {
                        "current_recv": float(parts[1]),
                        "peak_recv": float(parts[2]),
                        "current_send": float(parts[3]),
                        "peak_send": float(parts[4]),
                    }
                except ValueError:
                    continue # Skip line if conversion fails
    
    status_data["network_statistics"] = net_stats
    results["data"]["status"] = status_data

    # Return the final JSON string
    return json.dumps(results, indent=4)

if __name__ == "__main__":
    json_output = parse_server_status_to_json()
    print(json_output)
