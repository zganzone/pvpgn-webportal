// --- helper ---
function secondsToDhms(seconds) {
  seconds = Number(seconds);
  const d = Math.floor(seconds / (3600*24));
  const h = Math.floor((seconds % (3600*24))/3600);
  const m = Math.floor((seconds % 3600)/60);
  const s = Math.floor(seconds % 60);
  let str = '';
  if(d>0) str += d+'d ';
  if(h>0) str += h+'h ';
  if(m>0) str += m+'m ';
  str += s+'s';
  return str;
}

// --- fetch text helper (помага за server_uptime.txt и d2gs_uptime.txt) ---
async function fetchText(path) {
    const r = await fetch(path + '?_=' + Date.now()); 
    if(!r.ok) return null;
    return await r.text();
}

// --- Class Translation Helper ---
function translateClass(shortName) {
    const map = {
        'AMA': 'Amazon', 'BAR': 'Barbarian', 'NEC': 'Necromancer', 
        'PAL': 'Paladin', 'SOR': 'Sorceress', 'DRU': 'Druid', 
        'AS': 'Assassin', 'ZGANSASIN': 'Assassin', 'SORSI SOR': 'Sorceress', 'ASS': 'Assassin' 
    };
    const cleanName = shortName.toUpperCase().trim().replace(/\s/g, ''); 
    return map[cleanName] || shortName; 
}


// --- load server info (зарежда uptime) ---
async function loadServerUptime() {
    // 1. Server Uptime (КОРИГИРАН ПЪТ: data/server_uptime.txt)
    try {
        const serverTxt = await fetchText('data/server_uptime.txt');
        const sec = parseInt(serverTxt.trim()) || 0;
        document.getElementById('server-uptime').textContent = secondsToDhms(sec);
    } catch(e) {
        document.getElementById('server-uptime').textContent = 'N/A';
    }
    
    // 2. PvPGN Uptime (Пътът data/games.txt вече беше коректен)
    try {
        const resp = await fetch('data/games.txt'); 
        const text = await resp.text();
        const parser = new DOMParser();
        const xml = parser.parseFromString(text, "text/xml");
        const pvpgn_uptime_sec = parseInt(xml.querySelector('server > uptime').textContent);
        document.getElementById('pvpgn-uptime').textContent = secondsToDhms(pvpgn_uptime_sec);
    } catch(e) {
        console.error("Error loading PvPGN Uptime:", e);
        document.getElementById('pvpgn-uptime').textContent = 'Error';
    }

    // 3. D2GS Uptime (КОРИГИРАН ПЪТ: data/d2gs_uptime.txt)
    try {
        const d2gsTxt = await fetchText('data/d2gs_uptime.txt');
        const sec = parseInt(d2gsTxt.trim()) || 0;
        document.getElementById('d2gs-uptime').textContent = secondsToDhms(sec);
    } catch(e) {
        document.getElementById('d2gs-uptime').textContent = 'N/A';
    }
}

loadServerUptime(); 


// --- load games info (Пътят data/all_games.json вече е коректен) ---
fetch('data/all_games.json')
  .then(resp => resp.json())
  .then(games => {
    const container = document.getElementById('games-container');
    const now = new Date().toLocaleString();
    document.getElementById('last-updated').textContent = now;

    games.forEach(game => {
      const info = game.GameInfo;
      const div = document.createElement('div');
      let diff = info.Difficult.toLowerCase();
      if(diff != 'normal' && diff != 'nightmare' && diff != 'hell') diff = 'normal';
      div.className = 'game-card ' + diff;

      div.innerHTML = `<div class="game-title">${info.GameName} (${info.Difficult}) - ${info.UserCount} player(s)</div>`;

      if(game.Characters && game.Characters.length>0){
        let table = `<table class="players-table"><tr><th>Name</th><th>Class</th><th>Level</th><th>EnterTime</th></tr>`;
        game.Characters.forEach(ch => {
            const className = translateClass(ch.Class); 
            table += `<tr>
              <td><a href="charinfo.html?name=${ch.CharName.toLowerCase()}" target="_blank">${ch.CharName}</a></td> 
              <td>${className}</td> 
              <td>${ch.Level}</td>
              <td>${ch.EnterTime}</td>
            </tr>`;
        });
        table += '</table>';
        div.innerHTML += table;
      }
      container.appendChild(div);
    });
  });
