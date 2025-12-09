// =======================================================
// js/d2gs_status.js - Скрипт за зареждане и показване на D2GS status
// =======================================================

// Уверете се, че това е верният ПЪТ от корена на вашия уеб сървър
const JSON_FILE_URL = '/data/d2gs_status_latest.json'; 

// Функция за актуализиране на елемент
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// Основна функция за изтегляне и парсване на JSON данните
function fetchAndDisplayD2GSStatus() {
    
    // Първоначално задаваме статус "Loading"
    updateElement('d2gs-uptime', '...');

    fetch(JSON_FILE_URL)
        .then(response => {
            if (!response.ok) {
                // Ако файлът не е намерен (напр. 404), предполагаме Offline
                throw new Error(`HTTP Error: ${response.status} - Could not find JSON file at ${JSON_FILE_URL}`);
            }
            return response.json();
        })
        .then(data => {
            // Проверка за вътрешния статус на парсера
            if (data.status === "success" && data.data && data.data.uptime) {
                
                // Взимане на Uptime продължителността
                const uptimeDuration = data.data.uptime.uptime_duration || 'N/A';
                
                // --- АКТУАЛИЗИРАНЕ НА HTML ПОЛЕТАТА ---
                
                // 1. D2GS Uptime (в секцията summary)
                updateElement('d2gs-uptime', uptimeDuration);
                
                // Ако имате други полета за D2GS, добавете ги тук.
                // Например, ако добавите <p id="d2gs-users-online"></p>
                // updateElement('d2gs-users-online', data.data.status.current_activity.users_in_game);

                console.log("D2GS Uptime updated successfully:", uptimeDuration);

            } else {
                // Грешка в JSON (напр. Python скриптът не е успял да се свърже с D2GS)
                console.error("D2GS JSON reports internal error:", data.message || "Unknown error.");
                updateElement('d2gs-uptime', 'Error/Offline');
            }
        })
        .catch(error => {
            // Грешка при мрежата или JSON парсването
            console.error("Failed to fetch D2GS status:", error.message);
            updateElement('d2gs-uptime', 'Offline');
        });
}

// 1. Изпълнение на функцията веднага след зареждане на DOM
document.addEventListener('DOMContentLoaded', fetchAndDisplayD2GSStatus);

// 2. Обновяване на статуса на всеки 30 секунди (за да е актуален)
setInterval(fetchAndDisplayD2GSStatus, 30000);
