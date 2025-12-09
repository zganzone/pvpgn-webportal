#!/usr/bin/env python3
"""
PvPGN item report - JSON generation only.
Gathers and categorizes all items (inventory + stash) from all characters 
and outputs a single JSON file (data/all_items.json).
"""
from d2lib.files import D2SFile
import os, glob, json
from datetime import datetime
from collections import defaultdict

# === Configuration ===
# Пътища, базирани на Вашата структура
CHAR_DIR = "/usr/local/pvpgn/var/pvpgn/charsave"
CHARINFO_DIR = "/usr/local/pvpgn/var/pvpgn/charinfo"
OUTPUT_JSON = "/var/www/html/data/all_items.json" # <-- Новият целеви JSON файл

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

# === GATHER DATA ===
rows = []
print(f"[*] Starting item data collection from {CHAR_DIR}...")

for path in sorted(glob.glob(os.path.join(CHAR_DIR, "*"))):
    try:
        d2s = D2SFile(path)
    except Exception:
        print(f"[!] Skipping unreadable file: {os.path.basename(path)}")
        continue

    char_fname = os.path.basename(path)
    char_name = getattr(d2s, "name", None) or char_fname
    account_name = find_account_for_character(char_fname)

    # Combine inventory + stash
    all_items = list(getattr(d2s, "items", []))
    stash_items = getattr(d2s, "stash", None)
    if stash_items:
        if isinstance(stash_items, list):
            all_items += stash_items
        else:
            try:
                all_items += list(stash_items)
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
            # ТУК Е БЕШЕ ГРЕШКАТА: categorizedized_items
            elif code_l.startswith("cm3"): categorized_items["charms_grand"].append(name or code) 
            else: categorized_items["charms_small"].append(name or code)
            continue

        # 4. General item type categorization (using mapping/heuristics)
        itype = detect_type_from_code_and_name(code, name)

        # Map to final category keys
        if itype == "ring": categorized_items["rings"].append(name)
        elif itype == "belt": categorized_items["belts"].append(name)
        elif itype == "amulet": categorized_items["amulets"].append(name)
        elif itype == "weapon": categorized_items["weapons"].append(name)
        elif itype in ("armor","helmet","shield"): categorized_items["armors"].append(name)
        elif itype.startswith("charm"): categorized_items["charms_small"].append(name) # Fallback charm
        else: categorized_items["other"].append(name)

    # Append row data, ensuring all keys exist for the JSON structure
    row_data = {
        "account": account_name,
        "charfile": char_fname,
        "charname": char_name,
        "unique_set": categorized_items["unique_set"],
        "runes": categorized_items["runes"],
        "rings": categorized_items["rings"],
        "belts": categorized_items["belts"],
        "amulets": categorized_items["amulets"],
        "charms_small": categorized_items["charms_small"],
        "charms_large": categorized_items["charms_large"],
        "charms_grand": categorized_items["charms_grand"],
        "weapons": categorized_items["weapons"],
        "armors": categorized_items["armors"],
        "other": categorized_items["other"],
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
