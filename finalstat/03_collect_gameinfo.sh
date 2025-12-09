#!/usr/bin/expect -f
# ---------------------------------------
# Collect detailed info for each game dynamically
# ---------------------------------------

set timeout 20
set logfile "/usr/local/pvpgn/tools/finalstat/logs/gameinfo_raw.txt"
log_file -a $logfile

# Read dynamic game list
set games_list_file "/usr/local/pvpgn/tools/finalstat/logs/games_list.txt"
set games [list]
if {[file exists $games_list_file]} {
    set f [open $games_list_file r]
    set content [read $f]
    close $f
    # Split by newline and remove empty lines
    foreach line [split $content "\n"] {
        if {$line ne ""} {
            lappend games $line
        }
    }
} else {
    puts "Game list file not found: $games_list_file"
    exit 1
}

# Spawn bnchat only once and keep session
spawn /usr/local/pvpgn/bin/bnchat --client=D2XP 192.168.88.41 6112

expect "Username:"
send "webstat\r"
expect "Password:"
send "aman\r"

sleep 1

# Iterate games and send /gameinfo
foreach g $games {
    puts "Collecting info for: $g"
    send "/gameinfo $g\r"
    sleep 2
}

# Exit cleanly
send "/exit\r"
expect eof
