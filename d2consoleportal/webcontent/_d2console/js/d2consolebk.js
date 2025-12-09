// d2console.js
const GAMES_JSON = 'data/all_games.json';
const GAMES_XML = 'data/games.txt';
const SERVER_UPTIME_FILE = 'server_uptime.txt';   // must be produced on server
const D2GS_UPTIME_FILE = 'd2gs_uptime.txt';      // placeholder (optional)
const CHARS_DIR = './'; // character jsons in root d2console (or adjust)

// --- helpers ---
function humanDuration(seconds) {
  seconds = Number(seconds) || 0;
  const months = Math.floor(seconds / (30*24*3600));
  seconds %= (30*24*3600);
  const days = Math.floor(seconds / 86400);
  seconds %= 86400;
  const hours = Math.floor(seconds / 3600);
  seconds %= 3600;
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  let parts = [];
  if (months) parts.push(months + 'mo');
  if (days) parts.push(days + 'd');
  if (hours) parts.push(hours + 'h');
  if (minutes) parts.push(minutes + 'm');
  parts.push(secs + 's');
  return parts.join(' ');
}
function numericOrDash(v){ if(v===null||v===undefined||v==='') return '-'; return v; }

// fetch JSON safe
async function fetchJSON(path){
  const r = await fetch(path + '?_=' + Date.now());
  if(!r.ok) return null;
  return await r.json();
}
async function fetchText(path){
  const r = await fetch(path + '?_=' + Date.now());
  if(!r.ok) return null;
  return await r.text();
}

// --- load servers (XML games.txt) & display summary card(s) ---
async function loadServers(){
  const txt = await fetchText(GAMES_XML);
  if(!txt){ console.warn('games.txt not found'); return; }
  const xml = (new DOMParser()).parseFromString(txt, 'application/xml');
  const servers = xml.getElementsByTagName('server');
  const container = document.getElementById('servers-container');
  container.innerHTML = '';

  for(let i=0;i<servers.length;i++){
    const s = servers[i];
    const location = s.getElementsByTagName('location')[0]?.textContent?.trim() || '-';
    const users = s.getElementsByTagName('users')[0]?.textContent?.trim() || '0';
    const games = s.getElementsByTagName('games')[0]?.textContent?.trim() || '0';
    const total_games = s.getElementsByTagName('total_games')[0]?.textContent?.trim() || '0';
    const logins = s.getElementsByTagName('logins')[0]?.textContent?.trim() || '0';
    const pvpgn_uptime = s.getElementsByTagName('uptime')[0]?.textContent?.trim() || '0';

    // format pvpgn uptime in human format (months/days etc)
    const pvpgnHuman = humanDuration(Number(pvpgn_uptime));

    // read server uptime file (seconds)
    let serverUptimeHuman = '-';
    try {
      const serverTxt = await fetchText(SERVER_UPTIME_FILE);
      if(serverTxt){
        const sec = parseInt(serverTxt.trim()) || 0;
        serverUptimeHuman = humanDuration(sec);
      }
    } catch(e){ /* ignore */ }

    // read d2gs placeholder
    let d2gsHuman = '-';
    try {
      const t = await fetchText(D2GS_UPTIME_FILE);
      if(t){ d2gsHuman = humanDuration(parseInt(t.trim())||0); }
    } catch(e){ /* ignore */ }

    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `<div class="inline">
      <span style="font-weight:800">${location}</span>
      <span>Users: ${users}</span>
      <span>Games: ${games}</span>
      <span>Total: ${total_games}</span>
      <span>Logins: ${logins}</span>
      <span>Server Uptime: ${serverUptimeHuman}</span>
      <span>PvPGN Uptime: ${pvpgnHuman}</span>
      <span>D2GS Uptime: ${d2gsHuman}</span>
    </div>`;
    container.appendChild(card);
  }

  // set last updated
  document.getElementById('last-updated').textContent = new Date().toLocaleString();
}

// --- load games and characters ---
async function loadGames(){
  const data = await fetchJSON(GAMES_JSON);
  if(!data){ console.warn('all_games.json missing'); return; }
  const container = document.getElementById('games-container');
  container.innerHTML = '';

  for(const game of data){
    const g = game.GameInfo || {};
    const chars = game.Characters || [];

    const gameDiv = document.createElement('div');
    const diff = (g.Difficult||'').toLowerCase();
    let diffClass = '';
    if(diff.includes('normal')) diffClass='normal-game';
    else if(diff.includes('night')) diffClass='nightmare-game';
    else if(diff.includes('hell')) diffClass='hell-game';
    gameDiv.className = 'game ' + diffClass;

    gameDiv.innerHTML = `<h2>${numericOrDash(g.GameName)} [ID: ${numericOrDash(g.GameID)}] - ${numericOrDash(g.Difficult)}</h2>
      <table>
        <tr><th>GameVer</th><td>${numericOrDash(g.GameVer)}</td></tr>
        <tr><th>GameType</th><td>${numericOrDash(g.GameType)}</td></tr>
        <tr><th>IsLadder</th><td>${numericOrDash(g.IsLadder)}</td></tr>
        <tr><th>UserCount</th><td>${numericOrDash(g.UserCount)}</td></tr>
        <tr><th>CreateTime</th><td>${numericOrDash(g.CreateTime)}</td></tr>
        <tr><th>Creator</th><td>${numericOrDash(g.CreatorAcct)} / ${numericOrDash(g.CreatorChar)}</td></tr>
      </table>`;

    // characters
    for(const c of chars){
      const charName = (c.CharName || '').toLowerCase();
      let charData = null;
      try { charData = await fetchJSON(charName + '.json'); } catch(e){ charData = null; }
      const ci = (charData && charData.character_info) ? charData.character_info : {};
      const ists = (charData && charData.item_stats) ? charData.item_stats : {};

      const charDiv = document.createElement('div');
      charDiv.className = 'character';
      charDiv.innerHTML = `<h3>${ci.name || c.CharName} (${ci.class || c.Class} - Level ${ci.level || c.Level})</h3>
        <table>
          <tr><th>AcctName</th><td>${ci.account_name || c.AcctName}</td></tr>
          <tr><th>IP</th><td>${c.IPAddress || '-'}</td></tr>
          <tr><th>EnterTime</th><td>${c.EnterTime || '-'}</td></tr>
        </table>
        <div class="inventory">
          ${Array(40).fill(0).map((_,i)=>`<div class="slot"></div>`).join('')}
        </div>
        <div class="item-stats">
          Total: ${ists.total_items || 0}, Normal: ${ists.normal || 0}, Magic: ${ists.magic || 0}, Set: ${ists.set || 0}, Unique: ${ists.unique || 0}
        </div>`;
      gameDiv.appendChild(charDiv);
    }

    container.appendChild(gameDiv);
  }
}

// --- init ---
document.addEventListener('DOMContentLoaded', () => {
  loadServers();
  loadGames();
});
