# PvPGN Webportal

This repo contains scripts and static web pages for PvPGN server statistics:
- `scripts/` — parsers and collectors (Python, expect, bash)
- `web/` — static pages (HTML/JS/CSS)
- `deploy/` — systemd / cron examples
- `docs/` — install & usage

## Quick start (development)
1. Clone repo:
   `git clone git@github.com:youruser/pvpgn-webportal.git`
2. Install python deps:
   `pip3 install -r requirements.txt`
3. Run parsers:
   `python3 scripts/01.parse_full.py`
4. Open `web/index2.html` in your browser (or copy to /var/www/html/webportal/)

## Contributing
- Make feature branches: `git checkout -b feature/parse-items`
- Open PR to `main` when ready.

-----------


Direcotry tree 
##
#system structure


/usr/local/pvpgn/tools/finalstat
/var/www/html/


##
#webstat dir and files that are used

/usr/local/pvpgn/tools/finalstat/logs/bnchat_raw.txt
/usr/local/pvpgn/tools/finalstat/logs/gameinfo_clean.txt
/usr/local/pvpgn/tools/finalstat/logs/gameinfo.json
/usr/local/pvpgn/tools/finalstat/logs/gameinfo_raw.txt
/usr/local/pvpgn/tools/finalstat/logs/games_list.txt

##
#pvpgn dir and files that are used

/usr/local/pvpgn/var/pvpgn/charinfo
/usr/local/pvpgn/var/pvpgn/charsave
/usr/local/pvpgn/var/pvpgn/ladders/d2ladder.xml"
/usr/local/pvpgn/var/pvpgn/logs/games.txt"
