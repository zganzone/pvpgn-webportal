import telnetlib
import re

HOST = "192.168.88.41"
PORT = 8888
PASSWORD = "abcd123"

def parse_server_status():
    """Свързва се със сървъра през Telnet и извлича информацията за uptime и status."""
    
    try:
        tn = telnetlib.Telnet(HOST, PORT, timeout=5)
        
        # 1. Влизане (Изпращане на паролата)
        # Очаква 'Password:' или подобен промпт
        tn.read_until(b"pass:", timeout=2) 
        tn.write(PASSWORD.encode('ascii') + b"\n")
        
        # 2. Изпълнение на 'uptime'
        tn.write(b"uptime\n")
        # Прочитане на изхода до следващия промпт 'D2GS>' или край
        uptime_raw = tn.read_until(b"D2GS>", timeout=2).decode('ascii')
        
        # 3. Изпълнение на 'status'
        tn.write(b"status\n")
        status_raw = tn.read_until(b"D2GS>", timeout=2).decode('ascii')
        
        tn.close()
        
    except Exception as e:
        return f"Грешка при свързване или изпълнение на командата: {e}"

    # --- Обработка на Uptime ---
    uptime_info = ""
    # Извличане на старта и продължителността
    server_started_match = re.search(r"The game server started at (.*)", uptime_raw)
    uptime_duration_match = re.search(r"uptime (.*)", uptime_raw)
    current_time_match = re.search(r"Now it is (.*)", uptime_raw)

    if server_started_match and uptime_duration_match:
        uptime_info += f"*** ⏰ Състояние на Сървъра (Общо) ***\n"
        uptime_info += f"* **Старт на Сървъра:** {server_started_match.group(1).strip()}\n"
        uptime_info += f"* **Продължителност (Uptime):** **{uptime_duration_match.group(1).strip()}**\n"
        if current_time_match:
             uptime_info += f"* **Текущо време:** {current_time_match.group(1).strip()}\n"
        uptime_info += "\n"

    # --- Обработка на Status (Технически детайли) ---
    technical_details = "\n*** ⚙️ Технически Детайли (D2GS Status) ***\n\n"
    
    # Регулярни изрази за основните статистики
    game_stats = re.findall(r"(Setting maximum game|Current running game|Current users in game|Maximum prefer users|Maximum game life|Connetion to D2CS|Connetion to D2DBS):?\s*(.*)", status_raw)
    
    # Таблица за Основните Статистики
    technical_details += "### Активност и Лимити\n"
    technical_details += "| Параметър | Стойност | Забележка |\n"
    technical_details += "| :--- | :--- | :--- |\n"
    
    # Добавяне на данните от game_stats
    for key, value in game_stats:
        key = key.replace("Connetion", "Connection") # Корекция на 'Connetion'
        
        if "maximum game" in key:
            technical_details += f"| Макс. игри | {value.strip()} | Максимален капацитет |\n"
        elif "running game" in key:
            technical_details += f"| **Текущи Игри** | **{value.strip()}** | Активни сесии |\n"
        elif "users in game" in key:
            technical_details += f"| **Текущи Потребители** | **{value.strip()}** | Активни играчи |\n"
        elif "prefer users" in key:
            technical_details += f"| Макс. препоръчит. потребители | {value.strip()} | Макс. натоварване |\n"
        elif "game life" in key:
            technical_details += f"| Макс. живот на играта | {value.strip()}s | Няма таймаут |\n"
        elif "D2CS" in key:
            technical_details += f"| **D2CS Връзка** | **{value.strip()}** | Сървър за чат/акаунти |\n"
        elif "D2DBS" in key:
            technical_details += f"| **D2DBS Връзка** | **{value.strip()}** | Сървър за база данни |\n"

    technical_details += "\n"

    # Регулярни изрази за CPU и Memory
    cpu_mem_stats = re.findall(r"(Physical memory usage|Virtual memory usage|Kernel CPU usage|User CPU usage):\s*([^\n]+)", status_raw)
    
    technical_details += "### Натоварване на Ресурсите\n"
    technical_details += "| Ресурс | Използване | Забележка |\n"
    technical_details += "| :--- | :--- | :--- |\n"
    
    for key, value in cpu_mem_stats:
        key = key.strip()
        value = value.strip()
        
        if "Physical memory usage" in key:
            note = "**Внимание:** Вероятно грешка в отчета" if "0.000MB" in value else "Използване на физическата RAM"
            technical_details += f"| Физическа памет | {value} | {note} |\n"
        elif "Virtual memory usage" in key:
            note = "**Внимание:** Вероятно грешка в отчета" if "0.000MB" in value else "Използване на виртуална памет"
            technical_details += f"| Виртуална памет | {value} | {note} |\n"
        elif "Kernel CPU usage" in key:
            note = "**Внимание:** Вероятно грешка в отчета или е неактивен" if "0.00%" in value else "Натоварване на ядрото"
            technical_details += f"| CPU (Ядро) | {value} | {note} |\n"
        elif "User CPU usage" in key:
            note = "**Внимание:** Вероятно грешка в отчета или е неактивен" if "0.00%" in value else "Натоварване на потребителски процеси"
            technical_details += f"| CPU (Потребител) | {value} | {note} |\n"
            
    technical_details += "\n"
    
    # Парсиране на мрежовата статистика (таблица)
    net_stats_match = re.search(r"Game Server Net Statistic:[\s\S]*?(RecvPkts.*RecvBytes\s*SendPkts.*SendBytes[\s\S]*?D2CS[\s\S]*?D2DBS[\s\S]*?RecvRate.*PeakSendRate[\s\S]*?D2CS[\s\S]*?D2DBS)", status_raw)

    if net_stats_match:
        technical_details += "### Мрежова Статистика (Net Statistic)\n"
        technical_details += "Данните по-долу показват общия трафик (KBytes/second).\n\n"
        
        # Разделяне на двете под-таблици (Pkts/Bytes и Rates)
        stats_text = net_stats_match.group(0)
        
        # Pkts/Bytes Таблица
        pkts_bytes_match = re.search(r"RecvPkts\s*RecvBytes\s*SendPkts\s*SendBytes([\s\S]*?)RecvRate", stats_text)
        if pkts_bytes_match:
            lines = pkts_bytes_match.group(1).strip().split('\n')
            
            technical_details += "#### Общ Трафик (Пакети/Байтове)\n"
            technical_details += "| Сървър | RecvPkts | RecvBytes | SendPkts | SendBytes |\n"
            technical_details += "| :--- | :--- | :--- | :--- | :--- | \n"
            
            for line in lines:
                parts = line.split()
                if len(parts) == 5:
                    technical_details += f"| {parts[0]} | {parts[1]} | {parts[2]} | {parts[3]} | {parts[4]} |\n"
            technical_details += "\n"
            
        # Rates Таблица
        rates_match = re.search(r"RecvRate\s*PeakRecvRate\s*SendRate\s*PeakSendRate([\s\S]*)$", stats_text, re.MULTILINE)
        if rates_match:
            lines = rates_match.group(1).strip().split('\n')
            
            technical_details += "#### Скорости на Трафика (KBytes/second)\n"
            technical_details += "| Сървър | RecvRate | PeakRecvRate | SendRate | PeakSendRate |\n"
            technical_details += "| :--- | :--- | :--- | :--- | :--- |\n"
            
            for line in lines:
                parts = line.split()
                if len(parts) == 5:
                    technical_details += f"| {parts[0]} | {parts[1]} | {parts[2]} | {parts[3]} | {parts[4]} |\n"


    return uptime_info + technical_details

if __name__ == "__main__":
    result = parse_server_status()
    print(result)
