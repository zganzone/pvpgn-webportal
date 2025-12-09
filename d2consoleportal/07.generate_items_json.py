#!/usr/bin/env python3
"""
PvPGN item report - JSON generation only. (FINAL STABLE PYTHON CODE)
Includes fixes for D2LIB attribute names (char_name, char_level), 
Stash Gold (stashed_gold), Progression, and item grouping/counting.
"""
from d2lib.files import D2SFile
import os, glob, json
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any

# === Configuration ===
CHAR_DIR = "/usr/local/pvpgn/var/pvpgn/charsave"
CHARINFO_DIR = "/usr/local/pvpgn/var/pvpgn/charinfo"
OUTPUT_JSON = "/var/www/html/data/all_items.json" 

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# === Item Type Mapping and Detection ===
CODE_TO_TYPE = {
    # amulet
    "amu": "amulet",
    # ring
    "rin": "ring",
    # belt
    "bel": "belt",
    # charm codes 
    "cm1": "charm_small", "cm2": "charm_large", "cm3": "charm_grand",
    # jewelry generic
    "jew": "jewelry",
    # weapons / armor (examples)
    "swd": "weapon", "swf": "weapon", "axe": "weapon",
    "bow": "weapon", "xbow": "weapon", "stf": "weapon", "bst": "weapon",
    # shields / armor
    "shd": "armor", "plt": "armor", "ht": "armor",
    # jewels / gems
    "gem": "gem", "gld": "gold", "tkp": "token",
    # books / tomes etc
    "tbk": "book",
    # other/skill items
    "uap": "helmet",
}

def detect_type_from_code_and_name(code, name):
    if not code: code = ""
    if not name: name = ""
    code = code.lower()
    name = name.lower()
    
    if code in CODE_TO_TYPE: return CODE_TO_TYPE[code]
    
    if "ring" in name or "band" in name: return "ring"
    if "amulet" in name or "gorget" in name or "neck" in name: return "amulet"
    if "belt" in name: return "belt"
    if "charm" in name or "annihilus" in name or "gheed" in name: return "charm"
    if "helm" in name or "crown" in name or "mask" in name: return "helmet"
    if "shield" in name: return "shield"
    
    for kw in ("sword","axe","mace","dagger","bow","crossbow","staff","polearm","spear","hammer"):
        if kw in name: return "weapon"
        
    for kw in ("armor","plate","mail","leather","chain","robe","shield"):
        if kw in name: return "armor"
        
    return "other"

# === Account Finder ===
def find_account_for_character(char_filename):
    try:
        for acc in os.listdir(CHARINFO_DIR):
            p = os.path.join(CHARINFO_DIR, acc)
            if not os.path.isdir(p): continue
            try:
                if char_filename in os.listdir(p):
                    return acc
            except Exception:
                continue
    except FileNotFoundError:
        pass
    return "Unknown"

# === Item Grouping (за да се покаже бройката в charinfo.html) ===
def group_and_format_list(item_list: List[str]) -> List[str]:
    counts = defaultdict(int)
    for item in item_list:
        counts[item] += 1
    
    formatted_list = []
    for name, count in sorted(counts.items()):
        if count > 1:
            formatted_list.append(f"{name} ({count})")
        else:
            formatted_list.append(name)
            
    return formatted_list

# === GATHER DATA ===
rows: List[Dict[str, Any]] = []
print(f"[*] Starting item data collection from {CHAR_DIR}...")

for path in sorted(glob.glob(os.path.join(CHAR_DIR, "*"))):
    try:
        d2s = D2SFile(path)
    except Exception:
        print(f"[!] Skipping unreadable file: {os.path.basename(path)}")
        continue

    char_fname = os.path.basename(path)
    
    # --- КОРЕКЦИЯ 1: Извличане на основни данни с коректните ключове ---
    char_name = getattr(d2s, "char_name", None) or char_fname # ИЗПОЛЗВАМЕ 'char_name'
    account_name = find_account_for_character(char_fname)
    
    # Вземаме всички атрибути за извличане на Gold/Stats
    char_attributes = getattr(d2s, "attributes", {})

    # --- КОРЕКЦИЯ 2: БЛОК ЗА СТАТИСТИКИ (ВКЛЮЧИТЕЛНО ФИКСА ЗА GOLD И PROGRESSION) ---
    stats = {
        "level": getattr(d2s, "char_level", 0),
        "class": getattr(d2s, "char_class", "N/A"),
        "is_hc": getattr(d2s, "is_hardcore", False),
        "is_ladder": getattr(d2s, "is_ladder", False),
        
        "strength": char_attributes.get('strength', 0),
        "dexterity": char_attributes.get('dexterity', 0),
        "vitality": char_attributes.get('vitality', 0),
        "energy": char_attributes.get('energy', 0),
        
        "life": char_attributes.get('life', 0),
        "max_life": char_attributes.get('max_life', 0),
        "mana": char_attributes.get('mana', 0),
        "max_mana": char_attributes.get('max_mana', 0),
        
        # ФИКС ЗА ЗЛАТОТО
        "gold_inv": char_attributes.get('gold', 0),         # Ключ за Инвентарно Злато
        "gold_stash": char_attributes.get('stashed_gold', 0), # Ключ за Злато в Склада
        
        # ДАННИ ЗА ПРОГРЕС
        "progression": getattr(d2s, "progression", None),
        "unused_skills": char_attributes.get('unused_skills', 0),
        "unused_stats": char_attributes.get('unused_stats', 0)
    }
    
    # --- Извличане на предмети (Items) ---
    all_items = list(getattr(d2s, "items", []))
    stash_items = getattr(d2s, "stash", None) # Опитваме се да вземем stash
    
    if stash_items:
        try:
            # Тъй като 'stash' може да е ItemsDataStorage, опитваме да го превърнем в list
            all_items.extend(list(stash_items))
        except Exception:
            pass
            
    # Categorize items
    categorized_items = defaultdict(list)
    
    for item in all_items:
        # Get attributes safely
        name = getattr(item, "name", "") or ""
        code = getattr(item, "code", "") or ""
        is_unique = getattr(item, "is_unique", False)
        is_set = getattr(item, "is_set", False)
        is_rune = getattr(item, "is_rune", False)
        rid = getattr(item, "rune_id", None)
        
        # 1. Unique/Set
        if is_unique:
            categorized_items["unique_set"].append({"name": name, "type": "unique"})
        elif is_set:
            categorized_items["unique_set"].append({"name": name, "type": "set"})

        # 2. Runes
        if is_rune or (rid is not None and not name):
            runes_name = name or (f"Rune ID {rid}" if rid is not None else "Rune (Unknown)")
            categorized_items["runes"].append(runes_name)
            continue
            
        # 3. Charms detection by code prefix (cm1/cm2/cm3)
        code_l = code.lower()
        if code_l.startswith("cm"):
            if code_l.startswith("cm1"): categorized_items["charms_small"].append(name or code)
            elif code_l.startswith("cm2"): categorized_items["charms_large"].append(name or code)
            elif code_l.startswith("cm3"): categorized_items["charms_grand"].append(name or code)
            else: categorized_items["charms_small"].append(name or code)
            continue

        # 4. General item type categorization (using mapping/heuristics)
        itype = detect_type_from_code_and_name(code, name)

        # Map to final category keys
        if itype == "ring": categorized_items["rings"].append(name)
        elif itype == "belt": categorized_items["belts"].append(name)
        elif itype == "amulet": categorized_items["amulets"].append(name) # <-- КОРЕКЦИЯТА Е ТУК
        elif itype == "weapon": categorized_items["weapons"].append(name)
        elif itype in ("armor","helmet","shield"): categorized_items["armors"].append(name)
        elif itype.startswith("charm"): categorized_items["charms_small"].append(name) # Fallback charm
        else: categorized_items["other"].append(name)

    # Append row data, ensuring all keys exist for the JSON structure
    row_data = {
        "account": account_name,
        "charfile": char_fname,
        "charname": char_name,
        
        # ДОБАВЯМЕ СТАТИСТИКИТЕ
        "char_stats": stats, 
        
        # ГРУПИРАМЕ ПРЕДМЕТИТЕ ПО БРОЙКИ
        "unique_set": categorized_items["unique_set"],
        "runes": group_and_format_list(categorized_items["runes"]),
        "rings": group_and_format_list(categorized_items["rings"]),
        "belts": group_and_format_list(categorized_items["belts"]),
        "amulets": group_and_format_list(categorized_items["amulets"]),
        "charms_small": group_and_format_list(categorized_items["charms_small"]),
        "charms_large": group_and_format_list(categorized_items["charms_large"]),
        "charms_grand": group_and_format_list(categorized_items["charms_grand"]),
        "weapons": group_and_format_list(categorized_items["weapons"]),
        "armors": group_and_format_list(categorized_items["armors"]),
        "other": group_and_format_list(categorized_items["other"]),
    }
    rows.append(row_data)

# === Save JSON export ===
final_json = {
    "generated": timestamp, 
    "rows": rows
}
try:
    with open(OUTPUT_JSON, "w", encoding="utf-8") as jf:
        json.dump(final_json, jf, ensure_ascii=False, indent=2)
    print(f"[+] JSON report generated successfully: {OUTPUT_JSON}")
except Exception as e:
    print(f"[!] Failed to write JSON file: {e}")
