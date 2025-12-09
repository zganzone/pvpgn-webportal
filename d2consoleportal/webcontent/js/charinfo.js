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
    return isNaN(num) || num === 0 ? '-' : new Intl.NumberFormat('en-US').format(num);
}

function translateClass(shortName) {
    const map = {
        'AMA': 'Amazon', 'BAR': 'Barbarian', 'NEC': 'Necromancer', 
        'PAL': 'Paladin', 'SOR': 'Sorceress', 'DRU': 'Druid', 
        'AS': 'Assassin', 'ZGANSASIN': 'Assassin', 'SORSI SOR': 'Sorceress', 'ASS': 'Assassin'
    };
    const clean = shortName.toUpperCase().trim().replace(/\s/g, ''); 
    return map[clean] || shortName; 
}

// --- Функции за извличане на данни (Остават същите) ---

async function getExperienceFromLadder(charName) {
    let xmlDoc;
    try {
        xmlDoc = await fetchXML('data/d2ladder.xml');
    } catch(e) { return null; }
    
    if (!xmlDoc) return null;
    
    const charNameLower = cleanCharName(charName); 
    let bestRankExp = null;
    let bestRank = Infinity;

    const ladderEntries = xmlDoc.querySelectorAll('ladder');
    
    for (const ladder of ladderEntries) {
        const ladderType = getXMLText(ladder, 'type');
        const typeId = parseInt(ladderType);

        if (typeId < 27 || typeId > 34) {
            continue; 
        }

        const charEntries = ladder.querySelectorAll('char');
        for (const entry of charEntries) {
            const nameElement = entry.querySelector('name');
            
            if (nameElement && cleanCharName(nameElement.textContent) === charNameLower) {
                const expElement = entry.querySelector('experience');
                const rankElement = entry.querySelector('rank');
                
                if (expElement && rankElement) {
                    const currentRank = parseInt(rankElement.textContent.trim());
                    
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


function getCharNameFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return cleanCharName(params.get('name')); 
}

function cleanCharName(name) {
    if (!name) return '';
    return name.toLowerCase().trim().replace(/\s+/g, '');
}

function findCharStats(charNameLower, allItemsData) {
    if (!allItemsData || !allItemsData.rows) return null;
    
    const targetRow = allItemsData.rows.find(row => 
        row.charname && cleanCharName(row.charname) === charNameLower
    );
    
    return targetRow; // Връща целия обект с items и stats
}

// --- НОВА ФУНКЦИЯ: Генериране на списък с предмети ---
function renderCategorizedItems(itemData) {
    let html = '<div class="details-grid item-details-grid">'; // Използваме същата grid структура

    const categories = [
        { key: 'unique_set', title: 'Unique & Set', cls: 'unique-set-item' },
        { key: 'runes', title: 'Runes', cls: 'rune-item' },
        { key: 'amulets', title: 'Amulets', cls: '' },
        { key: 'rings', title: 'Rings', cls: '' },
        { key: 'belts', title: 'Belts', cls: '' },
        { key: 'charms_small', title: 'Charms (Small)', cls: 'charm-item' },
        { key: 'charms_large', title: 'Charms (Large)', cls: 'charm-item' },
        { key: 'charms_grand', title: 'Charms (Grand)', cls: 'charm-item' },
        { key: 'weapons', title: 'Weapons', cls: '' },
        { key: 'armors', title: 'Armor/Helms', cls: '' },
        { key: 'other', title: 'Other/Potions', cls: 'potion-item' },
    ];
    
    let itemsFound = false;

    categories.forEach(cat => {
        const list = itemData[cat.key];
        
        // Unique/Set са специални обекти и трябва да се форматират
        const formattedList = (cat.key === 'unique_set') 
            ? list.map(item => `<span class='${item.type}'>${item.name}</span>`) 
            : list.map(name => `<span class='${cat.cls}'>${name}</span>`);

        if (list && list.length > 0) {
            itemsFound = true;
            html += `
                <div class="details-card category-card">
                    <h3>${cat.title} (${list.length})</h3>
                    <ul class="item-list">
                        ${formattedList.map(itemHtml => `<li>${itemHtml}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
    });

    html += '</div>';
    
    // Връщаме съдържанието, или съобщение, ако няма предмети
    return itemsFound ? html : '<p style="text-align:center; color:#a0a0a0;">No classified items found in inventory/stash (based on all_items.json).</p>';
}

// ---------------------------------------------


async function loadCharInfo() {
    const charName = getCharNameFromUrl();
    if (!charName) {
        document.getElementById('char-name').textContent = 'Error: Character name missing.';
        return;
    }
    
    // 1. Асинхронно зареждане на всички необходими данни
    const [charData, ladderExp, allItemsData] = await Promise.all([
        // Използваме името на героя за зареждане на charname.json
        fetchJSON(`data/${charName}.json`), 
        getExperienceFromLadder(charName),
        fetchJSON('data/all_items.json') // Източникът на всичко
    ]);

    // 2. Обработка на основните данни
    
    if (!charData || !charData.character_info) {
        document.getElementById('char-name').textContent = `Error: Data for ${charName} not found.`;
        document.getElementById('char-summary').textContent = `Trying to load from data/${charName}.json`;
        return;
    }
    
    const ci = charData.character_info;
    const ists = charData.item_stats || {};
    
    // Извличаме целия ред от all_items.json, който съдържа items и stats
    const allRowData = findCharStats(charName, allItemsData); 
    const newStats = allRowData ? allRowData.char_stats || {} : {};
    const itemLists = allRowData || {}; // Използваме целия обект за списъци с предмети
    
    const statsToUse = { ...ci, ...newStats }; 

    // 3. Попълване на UI
    
    // Life/Mana Fix
    const currentLife = statsToUse.life > 0 ? statsToUse.life : statsToUse.max_life;
    const currentMana = statsToUse.mana > 0 ? statsToUse.mana : statsToUse.max_mana;

    const experienceValue = ladderExp || numericOrDash(ci.experience); 
    
    // 3a. Заглавие
    const charLevel = numericOrDash(statsToUse.level);
    const charClass = translateClass(statsToUse.class || ci.class || 'Unknown');

    document.getElementById('char-name').textContent = ci.name || charName;
    document.getElementById('char-summary').innerHTML = `${charClass} — Level ${charLevel} (${ci.expansion_type || 'Classic'} / ${ci.mode || 'Softcore'})`;
    
    // 3b. Статистики за Предметите
    document.getElementById('item-stats-summary').innerHTML = `
        Total Items: ${ists.total_items || 0} | Normal: ${ists.normal || 0} | Magic: ${ists.magic || 0} | Set: ${ists.set || 0} | Unique: ${ists.unique || 0}
    `;

    // 3c. Детайли за Героя
    document.getElementById('char-details').innerHTML = `
        <div class="stat-item"><span>Account</span><span>${numericOrDash(ci.account_name)}</span></div>
        <div class="stat-item"><span>Experience</span><span>${experienceValue}</span></div>
        <div class="stat-item"><span>Level</span><span>${charLevel}</span></div>
        <div class="stat-item"><span>Gold (Inv)</span><span>${numericOrDash(statsToUse.gold)}</span></div>
        <div class="stat-item"><span>Gold (Stash)</span><span>${numericOrDash(ci.gold_stash)}</span></div>
        <div class="stat-item"><span>Last Played</span><span>${numericOrDash(ci.last_played)}</span></div>
    `;

    // 3d. Основни Атрибути
    document.getElementById('attributes').innerHTML = `
        <div class="stat-item"><span>Strength</span><span>${numericOrDash(statsToUse.strength)}</span></div>
        <div class="stat-item"><span>Dexterity</span><span>${numericOrDash(statsToUse.dexterity)}</span></div>
        <div class="stat-item"><span>Vitality</span><span>${numericOrDash(statsToUse.vitality)}</span></div>
        <div class="stat-item"><span>Energy</span><span>${numericOrDash(statsToUse.energy)}</span></div>
        <div class="stat-item"><span>Life / Mana</span><span>${numericOrDash(currentLife)} / ${numericOrDash(currentMana)}</span></div>
    `;
    
    // 3e. ГЕНЕРИРАНЕ НА СПИСЪК С ПРЕДМЕТИ
    const itemListsContainer = document.getElementById('categorized-items-list');
    if (itemListsContainer) {
        itemListsContainer.innerHTML = renderCategorizedItems(itemLists);
    }
    
    // 3f. Инвентар (Grid) - Оставяме празен placeholder
    const inventoryGrid = document.getElementById('inventory-grid');
    inventoryGrid.innerHTML = Array(40).fill(0).map((_,i)=>`<div class="slot"></div>`).join('');
}

document.addEventListener('DOMContentLoaded', loadCharInfo);
