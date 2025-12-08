#!/bin/bash
##
#
rm /usr/local/pvpgn/tools/finalstat/logs/*
echo -n >  /usr/local/pvpgn/tools/finalstat/logs/bnchat_raw.txt
echo -n > /usr/local/pvpgn/tools/finalstat/logs/games_list.txt
sleep 1

/usr/local/pvpgn/tools/finalstat/01_collect_games.sh
sleep 1
/usr/local/pvpgn/tools/finalstat/02_clear_games.sh
/usr/local/pvpgn/tools/finalstat/03_collect_gameinfo.sh
sleep 1
/usr/local/pvpgn/tools/finalstat/04_clean_gamesinfo.sh
python3 /usr/local/pvpgn/tools/finalstat/05_build_json.py
sleep 1
python3  /usr/local/pvpgn/tools/finalstat/06_build_html.py
sleep 1
python3  /usr/local/pvpgn/tools/finalstat/z1.weball_new.py
sleep 1 
python3 /usr/local/pvpgn/tools/finalstat/07_build_ladder.py
#sleep 1
#python3  /usr/local/pvpgn/tools/finalstat/z2.weball_new.py



