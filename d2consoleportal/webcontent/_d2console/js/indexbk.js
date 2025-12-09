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
function translateClass(shortName) {
    const map = {
        'AMA': 'Amazon',
        'BAR': 'Barbarian',
        'NEC': 'Necromancer',
        'PAL': 'Paladin',
        'SOR': 'Sorceress',
        'DRU': 'Druid',
        'AS': 'Assassin',
        // Добавете съкращенията, които сте посочили, ако не са стандартните трибуквени
        'ZGANSASIN': 'Assassin', 
        'SORSI SOR': 'Sorceress',
        // 'ASS' често се използва за Assassin, ако е нужно
        'ASS': 'Assassin' 
    };
    // Премахва интервали, преобразува в горен регистър за по-добро съвпадение
    const cleanName = shortName.toUpperCase().trim(); 
    return map[cleanName] || shortName; // Връща пълното име или оригиналното, ако няма съвпадение
}


// --- load games info ---
fetch('all_games.json')
  .then(resp => resp.json())
  .then(games => {
    const container = document.getElementById('games-container');
    const now = new Date().toLocaleString();
    document.getElementById('last-updated').textContent = now;

    games.forEach(game => {
// ...
// (Останалата част за game info остава непроменена)
// ...

      if(game.Characters && game.Characters.length>0){
        let table = `<table class="players-table"><tr><th>Name</th><th>Class</th><th>Level</th><th>EnterTime</th></tr>`;
        game.Characters.forEach(ch => {
            // !!! ТУК ПРИЛАГАМЕ ФУНКЦИЯТА ЗА ПРЕВОД
            const className = translateClass(ch.Class);
            
            table += `<tr>
            <td>${ch.CharName}</td>
            <td>${className}</td> <--- ИЗПОЛЗВАМЕ ПРЕВЕДЕНОТО ИМЕ
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
// --- fetch text helper (similar to d2console.js) ---
async function fetchText(path) {
    // Използваме Date.now() за да предотвратим кеширане
    const r = await fetch(path + '?_=' + Date.now()); 
    if(!r.ok) return null;
    return await r.text();
}

// --- load server info ---
async function loadServerUptime() {
    // 1. PvPGN Uptime (от data/games.txt - XML)
    try {
        // !!! Променете пътя на 'data/games.txt'
        const resp = await fetch('data/games.txt'); 
        const text = await resp.text();
        const parser = new DOMParser();
        const xml = parser.parseFromString(text, "text/xml");
        // Предполагаме, че структурата е <server><uptime>...</uptime></server>
        const pvpgn_uptime_sec = parseInt(xml.querySelector('server > uptime').textContent);
        document.getElementById('pvpgn-uptime').textContent = secondsToDhms(pvpgn_uptime_sec);
    } catch(e) {
        // Ако грешката продължава, това ще помогне за дебъг
        console.error("Error loading PvPGN Uptime:", e); 
        document.getElementById('pvpgn-uptime').textContent = 'Error';
    }

    // 2. Server Uptime (от server_uptime.txt - Текст)
    // Запазваме същия път, който работи за Вас
    try {
        const serverTxt = await fetchText('server_uptime.txt');
        const sec = parseInt(serverTxt.trim()) || 0;
        document.getElementById('server-uptime').textContent = secondsToDhms(sec);
    } catch(e) {
        document.getElementById('server-uptime').textContent = 'N/A';
    }

    // 3. D2GS Uptime (от d2gs_uptime.txt - Текст)
    // Остава N/A, ако файлът липсва или е празен
    try {
        const d2gsTxt = await fetchText('d2gs_uptime.txt');
        const sec = parseInt(d2gsTxt.trim()) || 0;
        document.getElementById('d2gs-uptime').textContent = secondsToDhms(sec);
    } catch(e) {
        document.getElementById('d2gs-uptime').textContent = 'N/A';
    }
}

loadServerUptime(); // Извикваме новата функция при зареждане.

// --- load games info (запазваме оригиналната логика за игрите) ---
fetch('all_games.json')
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
          table += `<tr>
            <td>${ch.CharName}</td>
            <td>${ch.Class}</td>
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
