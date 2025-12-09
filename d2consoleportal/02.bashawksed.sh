cat logs/d2gs_gl_raw.txt | grep -w N | sed 's/ /_/g' | sed s'/_\+/|/g' | sed 's/||/|/g' | awk -F "|" '{print $4}' > logs/game_ready_ids.txt
echo "Game id file"
echo "logs/game_ready_ids.txt"
cat logs/game_ready_ids.txt
