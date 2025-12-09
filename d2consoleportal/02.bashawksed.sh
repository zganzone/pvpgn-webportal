cat /usr/local/pvpgn/tools/d2consoleportal/logs/d2gs_gl_raw.txt | grep -w N | sed 's/ /_/g' | sed s'/_\+/|/g' | sed 's/||/|/g' | awk -F "|" '{print $4}' > /usr/local/pvpgn/tools/d2consoleportal/logs/game_ready_ids.txt
echo "Game id file"
echo "/usr/local/pvpgn/tools/d2consoleportal/logs/game_ready_ids.txt"
cat /usr/local/pvpgn/tools/d2consoleportal/logs/game_ready_ids.txt
