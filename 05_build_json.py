#!/usr/bin/env python3
"""
Parse cleaned game info and build JSON
- Input: gameinfo_clean.txt
- Output: gameinfo.json
"""

import json
import time
import re
import os

# ----------------------------
# CONFIG
# ----------------------------
RAW_FILE = "/usr/local/pvpgn/tools/finalstat/logs/gameinfo_clean.txt"
JSON_FILE = "/usr/local/pvpgn/tools/finalstat/logs/gameinfo.json"

# ----------------------------
# Regex patterns
# ----------------------------
re_name       = re.compile(r'<Info>\s*Name:\s*(.+?)\s+ID:')
re_owner      = re.compile(r'<Info>\s*Owner:\s*(.+)')
re_address    = re.compile(r'<Info>\s*Address:\s*(.+)')
re_client     = re.compile(r'<Info>\s*Client:\s*(.+)')
re_created    = re.compile(r'<Info>\s*Created:\s*(.*)')
re_started    = re.compile(r'<Info>\s*Started:\s*(.*)')
re_status     = re.compile(r'<Info>\s*Status:\s*(.+)')
re_type       = re.compile(r'<Info>\s*Type:\s*(.+)')
re_difficulty = re.compile(r'<Info>\s*Difficulty:\s*(.+)')
re_players    = re.compile(r'<Info>\s*Players:\s*(\d+)\s*current,\s*(\d+)\s*total,\s*(\d+)\s*max')

# ----------------------------
# PARSE FILE
# ----------------------------
games = {}
current_game = None

if not os.path.exists(RAW_FILE):
    print(f"Error: {RAW_FILE} not found!")
    exit(1)

with open(RAW_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line.startswith("<Info>"):
            continue  # skip irrelevant lines

        # Start of a new game block
        if "<Info> Name:" in line:
            m = re_name.search(line)
            if m:
                current_game = m.group(1).strip()
                games[current_game] = {}
            else:
                current_game = None
            continue

        if current_game:
            # Match each field
            for pattern, key in [
                (re_owner, 'Owner'),
                (re_address, 'Address'),
                (re_client, 'Client'),
                (re_created, 'Created'),
                (re_started, 'Started'),
                (re_status, 'Status'),
                (re_type, 'Type'),
                (re_difficulty, 'Difficulty'),
                (re_players, ('Players_current', 'Players_total', 'Players_max'))
            ]:
                m = pattern.search(line)
                if m:
                    if isinstance(key, tuple):
                        games[current_game][key[0]] = int(m.group(1))
                        games[current_game][key[1]] = int(m.group(2))
                        games[current_game][key[2]] = int(m.group(3))
                    else:
                        games[current_game][key] = m.group(1).strip()

# ----------------------------
# BUILD JSON
# ----------------------------
data = {
    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    "games": games
}

# Write JSON atomically
tmp_file = JSON_FILE + ".tmp"
with open(tmp_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

os.replace(tmp_file, JSON_FILE)
print(f"Parsed {len(games)} games into {JSON_FILE}")

