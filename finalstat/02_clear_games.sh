#!/bin/bash
# ---------------------------------------
# Clean raw bnchat output and extract game names
# ---------------------------------------

RAW_FILE="/usr/local/pvpgn/tools/finalstat/logs/bnchat_raw.txt"
CLEAN_FILE="/usr/local/pvpgn/tools/finalstat/logs/gameinfo_clean.txt"
GAMES_LIST="/usr/local/pvpgn/tools/finalstat/logs/games_list.txt"

# Remove ^M, trim spaces, remove leading ']', keep <Info> lines
awk '{
    gsub("\r","");          # remove ^M
    sub(/^[ \t]*\]/,"");    # remove leading ]
    sub(/^[ \t]+/,"");      # remove leading spaces
    sub(/[ \t]+$/,"");      # remove trailing spaces

    # Skip unwanted lines
    if ($0 ~ /Check this url/ || $0 ~ /^http:\/\// || $0 ~ /^\/channels/ || $0 ~ /^<Info>[ \t]*----/ || $0 ~ /^<Info>[ \t]*$/) next

    # Keep /gameinfo lines or <Info> lines with game info
    if ($0 ~ /^\/gameinfo/ || ($0 ~ /^<Info>/ && $0 ~ /[A-Za-z0-9]/)) print
}' "$RAW_FILE" > "$CLEAN_FILE"

echo "Cleaned gameinfo saved to: $CLEAN_FILE"

# Extract only game names (lines where second word is 'n' or 'p')
awk '/^<Info>[ \t]+[A-Za-z0-9]+[ \t]+[np] open/ {print $2}' "$CLEAN_FILE" > "$GAMES_LIST"

echo "Game list saved to: $GAMES_LIST"
