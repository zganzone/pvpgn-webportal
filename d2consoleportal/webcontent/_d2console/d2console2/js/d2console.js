// === PATHS ===
const gamesJSON = 'all_games.json';
const serverXML = 'games.txt';
const charsDir = './';

// === HELPER FUNCTIONS ===
async function fetchJSON(path) {
  const res = await fetch(path);
  return await res.json();
}
async function fetchXML(path) {
  const res = await fetch(path);
  const text = await res.text();
  return new DOMParser().parseFromString(text, "application/xml");
}
async function fetchCharJSON(name) {
  if (!name) return null;
  const fileName = name.toLowerCase() + '.json';
  try {
    const res = await fetch(charsDir + fileName);
    if (!res.ok) return null;
    return await res.json();
  } catch(e) { return null; }
}

// === FORMAT UPTIME ===
function formatUptime(seconds) {
    const d = Math.floor(seconds / 86400);
    seconds %= 86400;
    const h = Math.floor(seconds / 3600);
    seconds %= 3600;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    let str = '';
    if(d>0) str += d + 'd ';
    if(h>0) str += h + 'h ';
    if(m>0) str += m + 'm ';
    str += s + 's';
    return str;
}

// === DIFFICULTY CLASS ===
function diffClass(diff) {
  if(!diff) return '';
  const d = diff.toLowerCase();
  if(d.includes('normal')) return 'normal-game';
  if(d.includes('night')) return 'nightmare-game';
  if(d.includes('hell')) return 'hell-game';
  return '';
}

// === LOAD SERVERS ===
async function loadServers() {
  const xml = await fetchXML(serverXML);
  const servers = xml.querySelectorAll('server');
  const container = document.getElementById('servers-container');
  servers.forEach(s => {
    const uptimeSec = parseInt(s.querySelector('uptime')?.textContent || '0', 10);
    const card = document.createElement('div');
    card.classList.add('card');
    card.innerHTML = `
      <strong>${s.querySelector('location')?.textContent || '-'}</strong>
      <span>Users: ${s.querySelector('users')?.textContent || 0}</span>
      <span>Games: ${s.querySelector('games')?.textContent || 0}</span>
      <span>Total: ${s.querySelector('total_games')?.textContent || 0}</span>
      <span>Logins: ${s.querySelector('logins')?.textContent || 0}</span>
      <span>Uptime: ${formatUptime(uptimeSec)}</span>
    `;
    container.appendChild(card);
  });
  document.getElementById('last-updated').textContent = new Date().toLocaleString();
}

// === LOAD GAMES ===
async function loadGames() {
  const data = await fetchJSON(gamesJSON);
  const container = document.getElementById('games-container');

  for (const game of data) {
    const g = game.GameInfo;
    const chars = game.Characters || [];

    const gameDiv = document.createElement('div');
    gameDiv.classList.add('game', diffClass(g.Difficult));
    gameDiv.innerHTML = `<h2>${g.GameName} [ID: ${g.GameID}] - ${g.Difficult}</h2>
      <table>
        <tr><th>GameVer</th><td>${g.GameVer||'-'}</td></tr>
        <tr><th>GameType</th><td>${g.GameType||'-'}</td></tr>
        <tr><th>IsLadder</th><td>${g.IsLadder||'-'}</td></tr>
        <tr><th>UserCount</th><td>${g.UserCount||'-'}</td></tr>
        <tr><th>CreateTime</th><td>${g.CreateTime||'-'}</td></tr>
        <tr><th>Disable</th><td>${g.Disable||'-'}</td></tr>
        <tr><th>Creator</th><td>${g.CreatorAcct||'-'} / ${g.CreatorChar||'-'}</td></tr>
      </table>`;

    for(const c of chars) {
      const charData = await fetchCharJSON(c.CharName) || {};
      const info = charData.character_info || {};
      const items = charData.item_stats || {};

      const charDiv = document.createElement('div');
      charDiv.classList.add('character');
      charDiv.innerHTML = `
        <h3>${info.name||c.CharName} (${info.class||c.Class} - Level ${info.level||c.Level})</h3>
        <table>
          <tr><th>AcctName</th><td>${info.account_name||c.AcctName}</td></tr>
          <tr><th>IP</th><td>${c.IPAddress}</td></tr>
          <tr><th>EnterTime</th><td>${c.EnterTime}</td></tr>
        </table>
<div class="inventory">
  ${Array(items.total_items || 0).fill(0).map(() => `<div class="slot"></div>`).join('')}
</div>

        <div class="item-stats">
          Total: ${items.total_items||0}, Normal: ${items.normal||0}, Magic: ${items.magic||0}, Set: ${items.set||0}, Unique: ${items.unique||0}
        </div>
      `;
      gameDiv.appendChild(charDiv);
    }
    container.appendChild(gameDiv);
  }
}

// === INIT ===
loadServers();
loadGames();
