# --- start /home/support/git/pvpgn-webportal/newconsoled2/console_parser.py (ФИНАЛЕН) ---
#!/usr/bin/env python3
import json
import re
import telnetlib
from datetime import datetime
import time 
import os
from config import D2GS_HOST, D2GS_PORT, D2GS_PASS, JSON_STATUS, JSON_GAMES, BASE_DIR 
from pathlib import Path

TEMP_GL_FILE = BASE_DIR / "temp_gl_raw.txt"

class D2GSConsole:
    """
    Класа за комуникация с D2GS Telnet конзолата и парсиране на изхода.
    """
    def __init__(self):
        self.host = D2GS_HOST
        self.port = D2GS_PORT
        self.password = D2GS_PASS
        self.tn = None
    
    def __enter__(self):
        # 1. Свързване
        try:
            self.tn = telnetlib.Telnet(self.host, self.port, timeout=5)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Telnet host: {e}")

        # 2. Изчакай заглавния банер ("D2GS Console")
        self.tn.read_until(b"Console", timeout=5)
        
        # 3. Изпрати паролата, след като видиш "Password:"
        self.tn.read_until(b"Password:", timeout=5)
        self.tn.write(self.password.encode('ascii') + b"\n")

        # !!! ПАУЗА СЛЕД ПАРОЛАТА (1.0 сек) !!!
        time.sleep(1.0) 

        # 4. Четене до крайния prompt (>)
        output = self.tn.read_until(b">", timeout=5)
        
        if b"Wrong password" in output or b"Sorry!" in output:
             # Ако логването не е минало, правим втори опит
             self.tn.write(self.password.encode('ascii') + b"\n")
             output = self.tn.read_until(b">", timeout=5)
             if b"Wrong password" in output or b"Sorry!" in output:
                  raise ConnectionError("Failed to login to D2GS Telnet console. Check password.")
        
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.tn:
            self.tn.write(b"exit\n")
            self.tn.close()

    def run_command(self, command, timeout=5):
        """Изпълнява команда и връща суровия изход като стринг, със sleep."""
        # !!! ПАУЗА ПРЕДИ КОМАНДАТА (0.5 сек) !!!
        time.sleep(0.5) 
        self.tn.write(command.encode('ascii') + b"\n")
        
        # Четене докато не се появи отново CLI prompt (>)
        output = self.tn.read_until(b">", timeout=7).decode('ascii', 'ignore')
        
        # Премахване на ехото на командата и крайния prompt
        output = output.replace(command, "", 1).strip()
        if output.endswith(">"):
             output = output[:-1].strip()
        
        return output

    def get_server_status(self):
        """Извлича uptime, status и записва server_status.json."""
        status_raw = self.run_command("status")
        uptime_raw = self.run_command("uptime")

        status_data = {}
        for line in status_raw.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                status_data[key.strip()] = value.strip()
        
        uptime_match = re.search(r"uptime (.*)", uptime_raw)
        status_data['Uptime'] = uptime_match.group(1).strip() if uptime_match else None
        
        status_data['LastUpdateTime'] = datetime.now().isoformat()
        
        with open(JSON_STATUS, 'w') as f:
            json.dump(status_data, f, indent=2)
            
        print(f"[STATUS] Server status saved to {JSON_STATUS}")
        return status_data

    def parse_game_list(self, gl_raw):
        """
        Парсира изхода на 'gl' (Game List), като изпълнява Вашата логика за заместване 
        и филтриране (grep -w N).
        """
        game_ids = []
        
        table_lines = []
        # 1. Филтриране за редове, съдържащи 'N' и започващи с '|'
        for line in gl_raw.splitlines():
            if line.startswith("|") and "N" in line and not line.startswith("+-"):
                 table_lines.append(line.strip())

        for line in table_lines:
            
            # 1. & 2. Заменяме 1 или повече интервала с един '|'
            temp_line = re.sub(r'\s+', '|', line.strip())
            
            # 3. Премахваме дублиращите се '|'
            temp_line = re.sub(r'\|+', '|', temp_line)
            
            # Разделяне по "|"
            columns = temp_line.split('|')

            # ID-то се пада на 4-ти елемент (индекс 3)
            if len(columns) > 3: 
                game_id = columns[3].strip()
                if game_id.isdigit():
                    game_ids.append(game_id)
            
        return game_ids

    def get_game_list_and_info(self):
        """Извлича Game IDs, след това извлича CL информация за всяка игра."""
        
        gl_raw = self.run_command("gl")
        
        # Диагностичен файл
        temp_file_for_check = BASE_DIR / "DIAG_gl_raw_output.txt"
        with open(temp_file_for_check, 'w', encoding='utf-8') as f:
             f.write(gl_raw)
        print(f"[DIAG] GL raw output saved to {temp_file_for_check}")

        game_ids = self.parse_game_list(gl_raw)
        all_games_data = []
        
        print(f"[GAMES] Found {len(game_ids)} active games. Retrieving details...")
        
        for game_id in game_ids:
            # Изпълнение на cl <ID>
            cl_raw = self.run_command(f"cl {game_id}", timeout=10)
            
            # Парсиране на CL изхода
            game_data = self._parse_cl_output(cl_raw)
            game_data = self._calculate_xp_rate(game_data)
            
            all_games_data.append(game_data)
            
        with open(JSON_GAMES, 'w') as f:
            json.dump(all_games_data, f, indent=2)
            
        print(f"[GAMES] Processed {len(all_games_data)} games, saved to {JSON_GAMES}")
        return all_games_data
    
    def _parse_cl_output(self, raw_output):
        """Парсира суровия изход от 'cl <ID>' командата, като игнорира празни ключове."""
        game_info = {}
        characters = []
        lines = raw_output.splitlines()

        # 1. Парсиране на Header Info [Key : Value]
        header_pattern = re.compile(r'\[(.*?)\s*:\s*(.*?)\s*\]')
        for line in lines:
            for match in header_pattern.finditer(line):
                key = match.group(1).strip()
                val = match.group(2).strip()
                
                # КОРЕКЦИЯ: ИГНОРИРАНЕ НА ПРАЗНИ КЛЮЧОВЕ
                if key: 
                    game_info[key] = val if val else None

        # 2. Парсиране на Character Table (Базирано на фиксирани индекси)
        char_table_started = False
        for line in lines:
            if line.startswith("+-No"):
                char_table_started = True
                continue
            
            if char_table_started and line.startswith("|"):
                if line.startswith("+---") or line.strip() == "":
                    continue
                
                # Фиксираните индекси
                no = line[2:6].strip()
                acct = line[6:22].strip()
                charname = line[22:40].strip()
                ip = line[40:58].strip()
                cls = line[58:64].strip()
                lvl = line[64:72].strip()
                time = line[72:80].strip()
                
                if no and acct and charname:
                    characters.append({
                        "No": no,
                        "AcctName": acct,
                        "CharName": charname,
                        "IPAddress": ip,
                        "Class": cls,
                        "Level": lvl,
                        "EnterTime": time
                    })
        
        return {
            "GameInfo": game_info,
            "Characters": characters
        }

    def _calculate_xp_rate(self, game_data):
        """Изчислява XP Rate."""
        game_info = game_data.get("GameInfo", {})
        user_count_str = game_info.get("UserCount")
        
        try:
            user_count = int(user_count_str) if user_count_str else 0
        except ValueError:
            user_count = 0
            
        if user_count >= 1:
            xp_rate = (user_count + 1) / 2
        else:
            xp_rate = 1.0
            
        game_info["UserCount"] = user_count
        game_info["XPRateMultiplier"] = round(xp_rate, 2)
        xp_bonus_percent = (xp_rate - 1.0) * 100
        game_info["XPBonusPercent"] = f"+{round(xp_bonus_percent):.0f}%"
        game_data["GameInfo"] = game_info
        return game_data


def main():
    print(f"Connecting to D2GS Console at {D2GS_HOST}:{D2GS_PORT}...")
    try:
        with D2GSConsole() as console:
            console.get_server_status()
            console.get_game_list_and_info()

    except ConnectionError as e:
        print(f"Error: {e}")
        print("Please ensure the D2GS server is running and the Telnet port is correct and accessible.")
    except telnetlib.socket.timeout:
        print(f"Error: Telnet connection timed out to {D2GS_HOST}:{D2GS_PORT}. Check network connectivity.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}. If the Telnet connection fails repeatedly, it may be a network or host issue.")

if __name__ == "__main__":
    main()
# --- end console_parser.py ---
