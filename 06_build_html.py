#!/usr/bin/env python3
"""
PvPGN HTML report
- Dark neon theme
- Server summary on top (Players, Games, Total Games, Logins, Uptime)
- Games table below with difficulty color-coding
"""

import os
import html
import time
import json
import xml.etree.ElementTree as ET

# ----------------------------
# CONFIG
# ----------------------------
BNTRACKD_OUTPUT = "/usr/local/pvpgn/var/pvpgn/logs/games.txt"
JSON_FILE = "/usr/local/pvpgn/tools/finalstat/logs/gameinfo.json"
OUTPUT_HTML = "/var/www/html/index.html"
REALM_NAME = "DarkPsy"

DIFFICULTY_COLORS = {
    'normal': '#0f0',
    'nightmare': '#ff8c00',
    'hell': '#f00'
}

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def parse_single_server_xml(path):
    """Parse single <server> block from XML games.txt"""
    if not os.path.exists(path):
        return None
    content = open(path, "r", encoding="utf-8").read().strip()
    wrapped = "<root>" + content + "</root>"
    try:
        root = ET.fromstring(wrapped)
    except Exception as e:
        print("XML parse error:", e)
        return None
    s = root.find("server")
    if s is None:
        return None
    def get_int(tag):
        try:
            return int(s.findtext(tag, "0").strip())
        except:
            return 0
    return {
        "ip": s.findtext("address", "").strip(),
        "port": s.findtext("port", "").strip(),
        "location": s.findtext("location", "").strip(),
        "software": s.findtext("software", "").strip(),
        "version": s.findtext("version", "").strip(),
        "users": get_int("users"),
        "channels": get_int("channels"),
        "games": get_int("games"),
        "total_games": get_int("total_games"),
        "logins": get_int("logins"),
        "description": s.findtext("description", "").strip(),
        "platform": s.findtext("platform", "").strip(),
        "url": s.findtext("url", "").strip(),
        "contact_email": s.findtext("contact_email", "").strip(),
        "uptime": get_int("uptime")
    }

def fmt_uptime(seconds):
    try:
        s = int(seconds)
    except:
        return ""
    days, s = divmod(s, 86400)
    hours, s = divmod(s, 3600)
    minutes, s = divmod(s, 60)
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    if not parts: parts.append(f"{s}s")
    return " ".join(parts)

# ----------------------------
# HTML GENERATOR
# ----------------------------
def generate_html(server, games, path):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    uptime_str = fmt_uptime(server["uptime"])

    html_parts = []

    # Header + style
    html_parts.append(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{REALM_NAME} Realm Stats</title>
<style>
body {{
    font-family: 'Garamond', 'Times New Roman', serif;
    background-color: #1c1c1c; /* dark Diablo-style */
    color: #f5d083; /* warm gold text */
    margin: 18px;
}}

h1, h2 {{
    text-align: center;
    color: #f5d083;
    text-shadow: 2px 2px 4px #000;
}}

p.sub {{
    text-align: center;
    color: #f5d083;
    margin: 4px 0 18px 0;
    font-size: 0.95rem;
}}

.summary {{
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}}

.card {{
    background-color: #2b2b2b;
    padding: 16px 24px;
    border-radius: 8px;
    box-shadow: 0 0 15px rgba(245,208,131,0.5);
    text-align: center;
    min-width: 100px;
}}

.card h2 {{
    margin: 0;
    font-size: 1.1rem;
    color: #f5d083;
}}

.card p {{
    margin: 4px 0 0 0;
    font-size: 1.1rem;
    font-weight: bold;
    color: #fff;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    background-color: #2b2b2b;
    border: 2px solid #f5d083;
}}

th, td {{
    padding: 8px;
    border-bottom: 1px solid rgba(245,208,131,0.2);
    text-align: left;
    color: #f5d083;
}}

th {{
    background-color: #3a2f2f;
    text-shadow: 1px 1px 2px #000;
}}

tr:nth-child(even) {{
    background-color: #2e2b2b;
}}

tr:hover {{
    background-color: #5a3e1b;
    color: #fff;
    font-weight: bold;
}}
</style>
</head>
<body>
""")

    html_parts.append(f"<h1>{REALM_NAME} Realm Statistics</h1>")
    html_parts.append(f"<p class='sub'>Last updated: {now}</p>")
    html_parts.append(f'<p><a href="/webstat.html"><H1>Item Stats</h1></a></p>')
    html_parts.append(f'<p><a href="/webladder.html"><H1>Ladder Stats</h1></a></p>')



    # Summary panel
    html_parts.append(f"""
<div class="summary">
  <div class="card"><h2>Players</h2><p>{server['users']}</p></div>
  <div class="card"><h2>Games</h2><p>{server['games']}</p></div>
  <div class="card"><h2>Total Games</h2><p>{server['total_games']}</p></div>
  <div class="card"><h2>Logins</h2><p>{server['logins']}</p></div>
  <div class="card"><h2>Uptime</h2><p>{uptime_str}</p></div>
</div>
""")

    # Games table
    html_parts.append("<table>")
    html_parts.append("<tr><th>Name</th><th>Owner</th><th>Address</th><th>Created</th>"
                      "<th>Started</th><th>Status</th><th>Type</th><th>Difficulty</th>"
                      "<th>Players (current/total/max)</th></tr>")

    for name, g in games.items():
        diff = g.get("Difficulty","").lower()
        color = DIFFICULTY_COLORS.get(diff, "#fff")
        players = f"{g.get('Players_current',0)}" #/{g.get('Players_total',0)}/{g.get('Players_max',0)}"
        html_parts.append(
            f"<tr>"
            f"<td>{html.escape(name)}</td>"
            f"<td>{html.escape(g.get('Owner',''))}</td>"
            f"<td>{html.escape(g.get('Address',''))}</td>"
#            f"<td>{html.escape(g.get('Client',''))}</td>"
            f"<td>{html.escape(g.get('Created',''))}</td>"
            f"<td>{html.escape(g.get('Started',''))}</td>"
            f"<td>{html.escape(g.get('Status',''))}</td>"
            f"<td>{html.escape(g.get('Type',''))}</td>"
            f"<td style='color:{color};font-weight:bold'>{html.escape(g.get('Difficulty',''))}</td>"
            f"<td>{players}</td>"
            f"</tr>"
        )

    html_parts.append("</table></body></html>")

    # Write atomically
    tmp_file = path + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
        f.write("".join(html_parts))
    os.replace(tmp_file, path)
    print(f"HTML report generated: {path}")

# ----------------------------
# MAIN
# ----------------------------
def main():
    server = parse_single_server_xml(BNTRACKD_OUTPUT)
    if server is None:
        print("No server data parsed!")
        return

    if not os.path.exists(JSON_FILE):
        print("No gameinfo JSON found!")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    games = data.get("games", {})

    generate_html(server, games, OUTPUT_HTML)

if __name__ == "__main__":
    main()
