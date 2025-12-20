#!/usr/bin/env python3.10
"""
log_grep.py - Ищет слово в логах LNS проекта
Использование: python log_grep.py СЛОВО
Пример: python log_grep.py ERROR
Пример: python log_grep.py V_12V
"""

import sys
import json

# Задаем конкретные пути
TEXT_LOG = "/var/log/lns_project/device_monitor.log"
JSON_LOG = "/var/log/lns_project/device_data.json"

def search_in_json(word):
    """Умный поиск в JSON файле"""
    try:
        with open(JSON_LOG, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            for idx, entry in enumerate(data, 1):
                # Для слова ERROR: ищем только реальные ошибки (не null)
                if word == "error":
                    error_value = entry.get("error")
                    if error_value and error_value != "null" and str(error_value).lower() != "none":
                        print(f"device_data.json: запись #{idx}: ОШИБКА: {error_value}")
                        print(f"    Полная запись: {json.dumps(entry, ensure_ascii=False)}")
                
                # Для других слов: ищем в любом поле
                else:
                    for key, value in entry.items():
                        if value and word in str(value).lower():
                            print(f"device_data.json: запись #{idx}, поле '{key}': {value}")
                    
    except (FileNotFoundError, json.JSONDecodeError):
        # Файл не найден или не JSON
        pass

def main():
    # Проверяем аргумент
    if len(sys.argv) < 2:
        print("Укажите слово для поиска")
        print("Примеры:")
        print("  python log_grep.py ERROR    # Поиск ошибок")
        print("  python log_grep.py V_12V    # Поиск напряжения")
        print("  python log_grep.py A_1A     # Поиск тока")
        print("  python log_grep.py S_DSA123 # Поиск серийного номера")
        print("  python log_grep.py OK       # Поиск успешных операций")
        print("  python log_grep.py INFO     # Поиск информационных сообщений")
        return
    
    word = sys.argv[1].lower()
    
    print(f"Поиск '{word}' в логах...")
    print("-" * 60)
    
    found_anything = False
    
    # 1. Ищем в текстовом логе
    try:
        with open(TEXT_LOG, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if word in line.lower():
                    print(f"device_monitor.log:{i}: {line.strip()}")
                    found_anything = True
    except FileNotFoundError:
        print(f"Файл {TEXT_LOG} не найден")
    
    # 2. Ищем в JSON логе
    search_in_json(word)
    
    # 3. Если ничего не найдено
    if not found_anything:
        print("Совпадений не найдено.")
    
    print("-" * 60)

if __name__ == "__main__":
    main()
