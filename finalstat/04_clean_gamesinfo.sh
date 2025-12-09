#!/bin/bash
# ---------------------------------------
# Clean raw gameinfo output from bnchat
# ---------------------------------------

RAW_FILE="/usr/local/pvpgn/tools/finalstat/logs/gameinfo_raw.txt"
CLEAN_FILE="/usr/local/pvpgn/tools/finalstat/logs/gameinfo_clean.txt"

# Remove ^M, trim spaces, remove leading ']' and any garbage before <Info>
tr -d '\r' < "$RAW_FILE" \
    | sed 's/^[ \t]*]//; s/^[ \t]*//; s/[ \t]*$//' \
    | sed 's/^.*\(<Info>.*\)/\1/' \
    | grep "^<Info>" > "$CLEAN_FILE"

echo "Cleaned gameinfo saved to: $CLEAN_FILE"

