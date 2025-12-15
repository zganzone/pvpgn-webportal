# --- start /home/support/git/pvpgn-webportal/newconsoled2/char_parser.py (ФИНАЛНА КОДИРОВКА И HTML) ---
#!/usr/bin/env python3
import json
import re
import datetime
from pathlib import Path
import os
import subprocess
import time

# Импорт на пътищата от config
from config import CHARINFO_DIR, JSON_ALL_CHARS, HTML_LADDER, LOGS_DIR

def parse_charinfo_file(filepath):
    """
    Парсира PvPGN .charinfo файл, използвайки latin-1 кодировка.
    """
    char_data = {}
    
    # Файлът е във формата KEY=VALUE
    try:
        # Използваме 'latin-1'
        with open(filepath, 'r', encoding='latin-1') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    char_data[key.strip()] = value.strip()
    except Exception as e:
        print(f"[ERROR] Cannot read file {filepath}: {e}")
        return None

    # Извличане и нормализиране на ключови данни
    char_name = char_data.get('charname', filepath.name)
    account_name = char_data.get('acctname', filepath.parent.name)
    
    # Конвертиране на времеви печати
    try:
        creation_timestamp = int(char_data.get('createtime', 0))
        last_login_timestamp = int(char_data.get('lastlogin', 0))
        char_data['CreateTimeISO'] = datetime.datetime.fromtimestamp(creation_timestamp).isoformat()
        char_data['LastLoginISO'] = datetime.datetime.fromtimestamp(last_login_timestamp).isoformat()
    except (ValueError, TypeError):
        # Ако времето е 0, времевият печат е 1970-01-01T02:00:00. Приемаме го, за да не счупим JSON структурата.
        char_data['CreateTimeISO'] = datetime.datetime.fromtimestamp(0).isoformat()
        char_data['LastLoginISO'] = datetime.datetime.fromtimestamp(0).isoformat()

    # Конвертиране на числови данни
    for key in ['level', 'experience', 'gold', 'pvpgntime']:
        try:
            char_data[key] = int(char_data.get(key, 0))
        except ValueError:
            char_data[key] = 0

    return {
        'AccountName': account_name,
        'CharName': char_name,
        'Class': char_data.get('charclass', 'N/A'),
        'Level': char_data.get('level', 1),
        'Experience': char_data.get('experience', 0),
        'Gold': char_data.get('gold', 0),
        'LastLogin': char_data.get('LastLoginISO', 'N/A'),
        'IsLadder': char_data.get('ladder', 'no') == 'yes',
        'PvPGNTime': char_data.get('pvpgntime', 0),
        'RawData': char_data 
    }

def collect_all_characters():
    """
    Сканира CHARINFO_DIR рекурсивно за файловете на героите.
    """
    print(f"[DEBUG] Checking directory existence: {CHARINFO_DIR}")
    if not CHARINFO_DIR.is_dir():
        print(f"[ERROR] Character info directory not found: {CHARINFO_DIR}. Check path in config.py.")
        return []

    all_characters = []
    
    print(f"[CHARS] Scanning recursively for character files in subdirectories of {CHARINFO_DIR}")
    
    # Взимаме всички директории (акаунти) под CHARINFO_DIR
    account_dirs = [d for d in CHARINFO_DIR.iterdir() if d.is_dir()]
    
    total_files_found = 0

    for account_dir in account_dirs:
        for char_file in account_dir.iterdir():
            if char_file.is_file():
                total_files_found += 1
                char_data = parse_charinfo_file(char_file)
                if char_data:
                    all_characters.append(char_data)
                
    print(f"[DEBUG] Total files scanned: {total_files_found}")
    print(f"[CHARS] Found and successfully processed {len(all_characters)} characters.")
    return all_characters


def generate_ladder_html(ladder_chars):
    """
    Генерира прост HTML изглед на стълбицата.
    """
    sorted_chars = sorted(ladder_chars, 
                          key=lambda c: (c['Level'], c['Experience']), 
                          reverse=True)

    # !!! КОРЕКЦИЯ ТУК: Екраниране на къдравите скоби в CSS с {{ и }} !!!
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>PvPGN Diablo II Ladder</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #333; color: #eee; }}
        .container {{ width: 80%; margin: 20px auto; background-color: #222; padding: 20px; border-radius: 8px; }}
        h2 {{ color: #f90; border-bottom: 2px solid #555; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #444; }}
        th {{ background-color: #444; color: #fff; }}
        tr:hover {{ background-color: #383838; }}
        .rank {{ font-weight: bold; width: 50px; text-align: center; }}
        .lvl {{ width: 80px; text-align: center; }}
    </style>
</head>
<body>
<div class="container">
    <h2>🏆 Diablo II Ladder (Активни Герои)</h2>
    <p>Общо Ладър герои: {total_ladder}</p>
    <table>
        <thead>
            <tr>
                <th class="rank">#</th>
                <th>Герой</th>
                <th>Акаунт</th>
                <th>Клас</th>
                <th class="lvl">Ниво</th>
                <th>Експа</th>
                <th>Последен Логин</th>
            </tr>
        </thead>
        <tbody>
    """.format(total_ladder=len(sorted_chars))

    for i, char in enumerate(sorted_chars, 1):
        # Премахваме времевата част от LastLogin за по-чист изглед
        last_login_date = char['LastLogin'].split('T')[0]
        
        html_content += f"""
            <tr>
                <td class="rank">{i}</td>
                <td>{char['CharName']}</td>
                <td>{char['AccountName']}</td>
                <td>{char['Class']}</td>
                <td class="lvl">{char['Level']}</td>
                <td>{char['Experience']:,}</td>
                <td>{last_login_date}</td>
            </tr>
        """

    html_content += """
        </tbody>
    </table>
</div>
</body>
</html>
"""
    try:
        with open(HTML_LADDER, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"[LADDER] HTML ladder saved to {HTML_LADDER}")
    except Exception as e:
        print(f"[ERROR] Failed to write HTML ladder file: {e}")


def main():
    
    all_chars = collect_all_characters()
    
    if not all_chars:
        print("[WARNING] No characters found. Skipping JSON and HTML generation.")
        return

    # 1. Записване на всички герои в JSON
    try:
        with open(JSON_ALL_CHARS, 'w', encoding='utf-8') as f:
            json.dump(all_chars, f, indent=2)
        print(f"[JSON] All characters data saved to {JSON_ALL_CHARS}")
    except Exception as e:
        print(f"[ERROR] Failed to write All Characters JSON: {e}")
        return

    # 2. Генериране на стълбицата само с Ladder герои
    ladder_chars = [c for c in all_chars if c['IsLadder']]
    generate_ladder_html(ladder_chars)


if __name__ == "__main__":
    main()
# --- end char_parser.py (ФИНАЛНА КОДИРОВКА И HTML) ---
