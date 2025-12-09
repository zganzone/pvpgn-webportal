// --- helpers (Общи) ---
function numericOrDash(v){ if(v===null||v===undefined||v==='') return '-'; return v; }

async function fetchJSON(path){
  const r = await fetch(path + '?_=' + Date.now());
  if(!r.ok) return null;
  return await r.json();
}

async function fetchXML(path){
  try {
        const r = await fetch(path + '?_=' + Date.now());
        if (!r.ok) throw new Error(`HTTP Error: ${r.status} ${r.statusText}`);
        const text = await r.text();
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(text, 'application/xml');
        // Проверка за синтактични грешки
        if (xmlDoc.getElementsByTagName('parsererror').length > 0) throw new Error('XML Syntax Error');
        return xmlDoc;
    } catch(e) {
        console.error("Fetch/Parse Error for XML:", e);
        throw e; 
    }
}

function getXMLText(elem, tag) {
    const child = elem.querySelector(tag);
    if (child && child.textContent) {
        return child.textContent.trim();
    }
    return "";
}

function formatExperience(exp) {
    const num = parseInt(exp);
    // Връща тире, ако опитът е 0 или не е число
    return isNaN(num) || num === 0 ? '-' : new Intl.NumberFormat('en-US').format(num);
}

function translateClass(shortName) {
    const map = {
        'AMA': 'Amazon', 'BAR': 'Barbarian', 'NEC': 'Necromancer', 
        'PAL': 'Paladin', 'SOR': 'Sorceress', 'DRU': 'Druid', 
        'AS': 'Assassin', 'ZGANSASIN': 'Assassin', 'SORSI SOR': 'Sorceress', 'ASS': 'Assassin'
    };
    const cleanName = shortName.toUpperCase().trim().replace(/\s/g, ''); 
    return map[cleanName] || shortName; 
}
// ---------------------------------------------

// --- Логика за XML (КОРЕКЦИЯТА е ТУК) ---
async function getExperienceFromLadder(charName) {
    let xmlDoc;
    try {
        xmlDoc = await fetchXML('data/d2ladder.xml');
    } catch(e) {
        return null; 
    }
    
    if (!xmlDoc) return null;
    
    // Име, което търсим (винаги в малки букви)
    const charNameLower = charName.toLowerCase(); 
    let bestRankExp = null;
    let bestRank = Infinity;

    const ladderEntries = xmlDoc.querySelectorAll('ladder');
    
    for (const ladder of ladderEntries) {
        const ladderType = getXMLText(ladder, 'type');
        const typeId = parseInt(ladderType);

        // ФИЛТЪР: Търсим само във Expansion класации (ID 27 до 34)
        if (typeId < 27 || typeId > 34) {
            continue; 
        }

        const charEntries = ladder.querySelectorAll('char');
        for (const entry of charEntries) {
            const nameElement = entry.querySelector('name');
            
            // КЛЮЧОВА КОРЕКЦИЯ: Сравняваме името от XML (преобразувано в малки букви) с търсеното име (също в малки букви).
            if (nameElement && nameElement.textContent.trim().toLowerCase() === charNameLower) {
                const expElement = entry.querySelector('experience');
                const rankElement = entry.querySelector('rank');
                
                if (expElement && rankElement) {
                    const currentRank = parseInt(rankElement.textContent.trim());
                    
                    // Взимаме този с най-добрия ранг, за да избегнем дубликати
                    if (currentRank < bestRank) {
                        bestRank = currentRank;
                        bestRankExp = formatExperience(expElement.textContent.trim());
                    }
                }
            }
        }
    }
    
    return bestRankExp; 
}
// ---------------------------------------------


function getCharNameFromUrl() {
    const params = new URLSearchParams(window.location.search);
    // Името от URL се превръща в малки букви (напр. 'MFamazon' -> 'mfamazon')
    return (params.get('name') || '').toLowerCase(); 
}

async function loadCharInfo() {
    const charName = getCharNameFromUrl();
    if (!charName) {
        document.getElementById('char-name').textContent = 'Error: Character name missing.';
        return;
    }

    // Използваме името в малки букви за зареждане на JSON файла (напр. data/mfamazon.json)
    const [charData, ladderExp] = await Promise.all([
        fetchJSON(`data/${charName}.json`),
        getExperienceFromLadder(charName) 
    ]);


    if (!charData || !charData.character_info) {
        document.getElementById('char-name').textContent = `Error: Data for ${charName} not found.`;
        document.getElementById('char-summary').textContent = `Trying to load from data/${charName}.json`;
        return;
    }

    const ci = charData.character_info;
    const ists = charData.item_stats || {};
    const attr = charData.attributes || {};
    
    // Използваме опита, намерен в XML, или падаме на опита от JSON файла
    const experienceValue = ladderExp || numericOrDash(ci.experience); 
    
    // 1. Попълване на Заглавието
    const className = translateClass(ci.class || 'Unknown');
    // Използваме името от JSON за коректен регистър на дисплея (ci.name)
    document.getElementById('char-name').textContent = ci.name || charName;
    document.getElementById('char-summary').innerHTML = `${className} — Level ${numericOrDash(ci.level)} (${ci.expansion_type || 'Classic'} / ${ci.mode || 'Softcore'})`;
    
    // 2. Попълване на Статистиките за Предметите
    document.getElementById('item-stats-summary').innerHTML = `
        Total Items: ${ists.total_items || 0} | Normal: ${ists.normal || 0} | Magic: ${ists.magic || 0} | Set: ${ists.set || 0} | Unique: ${ists.unique || 0}
    `;

    // 3. Детайли за Героя (Details Card)
    document.getElementById('char-details').innerHTML = `
        <div class="stat-item"><span>Account</span><span>${numericOrDash(ci.account_name)}</span></div>
        <div class="stat-item"><span>Experience</span><span>${experienceValue}</span></div>
        <div class="stat-item"><span>Gold (Stash)</span><span>${numericOrDash(ci.gold_stash)}</span></div>
        <div class="stat-item"><span>Gold (On hand)</span><span>${numericOrDash(ci.gold_inventory)}</span></div>
        <div class="stat-item"><span>Last Played</span><span>${numericOrDash(ci.last_played)}</span></div>
    `;

    // 4. Основни Атрибути (Attributes Card)
    document.getElementById('attributes').innerHTML = `
        <div class="stat-item"><span>Strength</span><span>${numericOrDash(attr.strength)}</span></div>
        <div class="stat-item"><span>Dexterity</span><span>${numericOrDash(attr.dexterity)}</span></div>
        <div class="stat-item"><span>Vitality</span><span>${numericOrDash(attr.vitality)}</span></div>
        <div class="stat-item"><span>Energy</span><span>${numericOrDash(attr.energy)}</span></div>
        <div class="stat-item"><span>Life / Mana</span><span>${numericOrDash(attr.current_life)} / ${numericOrDash(attr.current_mana)}</span></div>
    `;
    
    // 5. Инвентар (Grid)
    const inventoryGrid = document.getElementById('inventory-grid');
    inventoryGrid.innerHTML = Array(40).fill(0).map((_,i)=>`<div class="slot"></div>`).join('');
}

document.addEventListener('DOMContentLoaded', loadCharInfo);
