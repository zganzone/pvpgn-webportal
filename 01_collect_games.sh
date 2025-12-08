#!/usr/bin/expect -f
set timeout 20
set logfile "/usr/local/pvpgn/tools/finalstat/logs/bnchat_raw.txt"

log_file -a $logfile

spawn /usr/local/pvpgn/bin/bnchat --client=D2XP 192.168.88.41 6112

expect "Username:"
send "webstat\r"
expect "Password:"
send "aman\r"

# Give server time to send welcome messages
sleep 1

# Commands to capture visible info
send "/players\r"
sleep 1
send "/games\r"
sleep 1
send "/channels\r"
sleep 1
send "/info\r"
sleep 1

# Exit cleanly
send "/exit\r"
expect eof
