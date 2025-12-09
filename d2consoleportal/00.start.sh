#!/bin/bash
rm /usr/local/pvpgn/tools/d2consoleportal/logs/cl_output/* -f
rm /usr/local/pvpgn/tools/d2consoleportal/logs/* -f

cp /usr/local/pvpgn/var/pvpgn/logs/games.txt /var/www/html/data/games.txt

cp /usr/local/pvpgn/var/pvpgn/ladders/d2ladder.xml /var/www/html/data/
sleep 1
/usr/local/pvpgn/tools/d2consoleportal/01.d2gs_get_gl.exp
sleep 1
/usr/local/pvpgn/tools/d2consoleportal/02.bashawksed.sh
sleep 1
/usr/local/pvpgn/tools/d2consoleportal/03.d2gs_cl_runner.sh
sleep 1
#python3 /usr/local/pvpgn/tools/d2consoleportal/05.gameinfo2json.py
python3 /usr/local/pvpgn/tools/d2consoleportal/05.gameinfo2json_v2.py
sleep 1
python3 /usr/local/pvpgn/tools/d2consoleportal/06_build_ladder.py
sleep 1
python3 /usr/local/pvpgn/tools/d2consoleportal/07.generate_items_json.py
/usr/local/pvpgn/tools/d2consoleportal/07.char2json -o /var/www/html/data/
python3 /usr/local/pvpgn/tools/d2consoleportal/08.d2gs_time_ands_status_json.py
/usr/local/pvpgn/tools/d2consoleportal/cronfile.sh
sleep 1
#python3 /usr/local/pvpgn/tools/d2consoleportal/10.charitemstat.py
