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
python3 /usr/local/pvpgn/tools/d2consoleportal/05.gameinfo2json.py
sleep 1
python3 /usr/local/pvpgn/tools/d2consoleportal/08_build_ladder.py
sleep 1
python3 /usr/local/pvpgn/tools/d2consoleportal/09.generate_items_json.py
/usr/local/pvpgn/tools/d2consoleportal/cronfile.sh
sleep 1
python3 /usr/local/pvpgn/tools/d2consoleportal/10.charitemstat.py
