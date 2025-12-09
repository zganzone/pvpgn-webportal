const JSON_URL = 'data/all_items.json';

// --- Helper functions ---

// Helper за форматиране на списъци с предмети
function joinSpan(list, className = "") {
    if (!list || list.length === 0) {
        return "<span class='empty'>—</span>";
    }
    // Ако елементите са обекти (като unique/set), извличаме името
    const formattedList = list.map(item => {
        const name = (typeof item === 'object' && item.name) ? item.name : item;
        const type = (typeof item === 'object' && item.type) ? item.type : className;
        
        // Преобразуване на типа в клас (unique, set, rune)
        const cls = (type === 'unique' || type === 'set' || type === 'rune') ? type : className;

        // Използваме Markdown escape за безопасност
        return `<span class='${cls}'>${escapeHTML(name)}</span>`;
    });

    return formattedList.join(", ");
}

// Helper за Escape на HTML символи
function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#39;');
}

// --- Main Logic ---
let itemsData = [];
const table = document.getElementById('itemsTable');
let sortCol = 'account';
let sortDir = 1; // 1 = ASC (A-Z), -1 = DESC (Z-A)

async function loadItemData() {
    try {
        const response = await fetch(JSON_URL);
        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status}`);
        }
        const data = await response.json();
        itemsData = data.rows;
        renderTable(itemsData);

    } catch (e) {
        const tbody = table.tBodies[0];
        tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; color:red;">
            Error loading item data from ${JSON_URL}. Check console: ${e.message}
        </td></tr>`;
        console.error("Item Data Load Error:", e);
    }
}

function renderTable(rows) {
    const tbody = table.tBodies[0];
    tbody.innerHTML = ''; // Изчистване на старото съдържание

    const palette = ["#ffffff","#fffbe6","#f7fff2","#eef7ff","#fff0f6","#f9f5ff"]; // Палитра за редовете
    const accToColor = {};
    const accList = [...new Set(rows.map(r => r.account))].sort();

    // Задаване на цвят по акаунт
    accList.forEach((acc, i) => {
        accToColor[acc] = palette[i % palette.length];
    });

    // Генериране на редовете
    rows.forEach(r => {
        const charnameLower = r.charname.toLowerCase();
        const color = accToColor[r.account] || "#ffffff";
        
        const usCell = joinSpan(r.unique_set);
        const runesCell = joinSpan(r.runes, "rune");
        const ringsCell = joinSpan(r.rings);
        const beltsCell = joinSpan(r.belts);
        const amuletsCell = joinSpan(r.amulets);
        
        const charmsCell = `S:${r.charms_small.length}, L:${r.charms_large.length}, G:${r.charms_grand.length}`;
        
        const weaponsCell = joinSpan(r.weapons);
        const armorsCell = joinSpan(r.armors);
        const otherCell = joinSpan(r.other);
        
        const row = tbody.insertRow();
        row.className = 'account-row';
        row.dataset.account = r.account;
        row.style.background = color;
        
        // Клетките
        row.innerHTML = `
            <td>${escapeHTML(r.account)}</td>
            <td><a href="charinfo.html?name=${charnameLower}" target="_blank">${escapeHTML(r.charname)}</a></td>
            <td>${usCell}</td>
            <td>${runesCell}</td>
            <td>${ringsCell}</td>
            <td>${beltsCell}</td>
            <td>${amuletsCell}</td>
            <td>${charmsCell}</td>
            <td>${weaponsCell}</td>
            <td>${armorsCell}</td>
            <td>${otherCell}</td>
        `;
    });
}


// --- Functionality (Sorting, Filtering, Export) ---

function getCellValue(row, colIndex) {
    // Връща текстовата стойност на клетката, като игнорира HTML
    const cell = row.cells[colIndex];
    if (cell) {
        // За charms, връщаме целия текст (S:X, L:Y, G:Z)
        if (colIndex === 7) return cell.innerText.trim();
        // За всички останали, връщаме чист текст (за сортиране)
        return cell.innerText.trim().toLowerCase();
    }
    return '';
}

function sortTableBy(col) {
    const headers = Array.from(table.tHead.querySelector('tr').cells);
    const colIndex = headers.findIndex(th => th.getAttribute('data-col') === col);
    if (colIndex === -1) return;

    // Смяна на посоката, ако кликнем на същата колона
    if (sortCol === col) {
        sortDir *= -1;
    } else {
        sortDir = 1;
        sortCol = col;
    }

    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    
    // Сортиране на редовете
    rows.sort((a, b) => {
        const aVal = getCellValue(a, colIndex);
        const bVal = getCellValue(b, colIndex);

        // Сортиране на числа (за Charms, Level, Experience) - макар че тук всички са текст
        if (!isNaN(parseInt(aVal)) && !isNaN(parseInt(bVal))) {
             return (parseInt(aVal) - parseInt(bVal)) * sortDir;
        }
        
        // Текстово сортиране
        if (aVal < bVal) return -1 * sortDir;
        if (aVal > bVal) return 1 * sortDir;
        return 0;
    });

    // Добавяне на редовете обратно в правилния ред
    for (let row of rows) {
        tbody.appendChild(row);
    }
}

function filterTable() {
    const q = document.getElementById('searchInput').value.toLowerCase();
    const rows = table.tBodies[0].rows;
    for (let r of rows) {
        // Търсене във вътрешния текст на целия ред
        const text = r.innerText.toLowerCase(); 
        r.style.display = text.indexOf(q) === -1 ? 'none' : '';
    }
}

function expandAll() {
    const rows = table.tBodies[0].rows;
    for (let r of rows) r.style.display = '';
}

function collapseAll() {
    const rows = table.tBodies[0].rows;
    for (let r of rows) r.style.display = 'none';
}

// Exports (Използваме експортираните файлове, генерирани от Python скрипта)
function exportJSON() {
    downloadFile('/data/items_export.json', 'items_export.json', 'application/json');
}

function exportCSV() {
    downloadFile('/data/items_export.csv', 'items_export.csv', 'text/csv');
}

function downloadFile(url, filename, mime) {
    fetch(url)
        .then(response => response.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        })
        .catch(e => alert(`Export failed. Check if ${filename} exists. Error: ` + e.message));
}


// --- Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    loadItemData();

    // Присвояване на събитието за сортиране към заглавките на таблицата
    document.querySelectorAll('#itemsTable th[data-col]').forEach(th => {
        th.addEventListener('click', () => {
            const col = th.getAttribute('data-col');
            sortTableBy(col);
        });
    });
});
