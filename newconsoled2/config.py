# --- start /home/support/git/pvpgn-webportal/newconsoled2/config.py ---
import os
from pathlib import Path

# --- DIRECTORY CONFIGURATION (PvPGN System Paths) ---
# Базова директория на скрипта (за да може да намираме DIAG файловете)
BASE_DIR = Path(__file__).parent  
LOGS_DIR = BASE_DIR / "logs"      # Директория за бъдещи логове

# --- D2GS TELNET CONFIGURATION ---
D2GS_HOST = "192.168.88.41"  # ВАШИЯ IP АДРЕС
D2GS_PORT = 8888             # ВАШИЯ ПОРТ
D2GS_PASS = "abcd123"        # ВАШАТА ПАРОЛА

# PVPGN FILE LOCATIONS (Фиксирани пътища за D2S файлове)
PVPGN_ROOT = "/usr/local/pvpgn/var/pvpgn"
CHARINFO_DIR = Path(PVPGN_ROOT) / "charinfo"
CHARSAVE_DIR = Path(PVPGN_ROOT) / "charsave"
LADDER_XML = Path(PVPGN_ROOT) / "ladders/d2ladder.xml"

# --- OUTPUT CONFIGURATION (Web Paths) ---
# Директория, където ще се записват JSON файловете за уеба
WEB_ROOT_DIR = Path("/var/www/html/newconsoled2/data")
# Създава директорията, ако не съществува
WEB_ROOT_DIR.mkdir(parents=True, exist_ok=True) 

# --- FINAL JSON FILE NAMES ---
JSON_GAMES = WEB_ROOT_DIR / "all_games.json"
JSON_STATUS = WEB_ROOT_DIR / "server_status.json"
JSON_ALL_CHARS = WEB_ROOT_DIR / "all_char_all_acc.json"
HTML_LADDER = Path("/var/www/html/webladder.html")
# --- end config.py ---
