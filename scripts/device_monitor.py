#!/usr/bin/env python3.10
"""
Скрипт мониторинга устройства с записью в лог
Запускается как сервис в Linux
"""

import sys
import os
# ========== ПРОВЕРКА ВЕРСИИ PYTHON ==========
MIN_PYTHON_VERSION = (3, 10)
if sys.version_info < MIN_PYTHON_VERSION:
    print(f"Требуется Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} или выше")
    print(f"Текущая версия: {sys.version}")
    sys.exit(1)
# ============================================
import time
import signal
import logging
import json
from datetime import datetime
from typing import Dict, Any
import yaml
from pathlib import Path

# Добавляем путь к модулю device
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from device.device_client import (
    DeviceClient, DeviceConfig, InterfaceType, 
    create_device_client, ConnectionError
)

class DeviceMonitor:
    """
    Монитор устройства для периодического опроса и логирования
    """
    
    def __init__(self, config_path: str = None):
        """
        Инициализация монитора
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        self.config = self._load_config(config_path)
        self.device = None
        self.is_running = False
        self.logger = self._setup_logging()
        
        # Обработчики сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("Монитор устройства инициализирован")
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """
        Загрузка конфигурации из файла
        
        Args:
            config_path: Путь к конфигурационному файлу
            
        Returns:
            Dict: Конфигурация
        """
        # Пути по умолчанию
        default_paths = [
            config_path,
            "/etc/device_monitor/config.yaml",
            str(Path.home() / ".config/device_monitor/config.yaml"),
            "config/default.yaml",
        ]
        
        for path in default_paths:
            if path and os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        config = yaml.safe_load(f)
                    self.logger = logging.getLogger(__name__)
                    self.logger.info(f"Загружена конфигурация из {path}")
                    return config
                except Exception as e:
                    print(f"Ошибка загрузки конфигурации из {path}: {e}")
        
        # Конфигурация по умолчанию
        default_config = {
            'device': {
                'interface': 'udp',
                'host': '127.0.0.1',
                'port': 10000,
                'serial_port': 'ttyACM0',
                'baudrate': 115200,
                'timeout': 5.0
            },
            'monitoring': {
                'period': 2.0,
                'log_file': 'device_data.json',
                'max_log_size_mb': 10,
                'max_log_files': 5
            },
            'logging': {
                'level': 'INFO',
                'file': 'device_monitor.log',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
        
        print("Используется конфигурация по умолчанию")
        return default_config
    
    def _setup_logging(self) -> logging.Logger:
        """
        Настройка логирования
        
        Returns:
            logging.Logger: Настроенный логгер
        """
        log_config = self.config.get('logging', {})
        
        logger = logging.getLogger('DeviceMonitor')
        logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))
        
        # Форматтер
        formatter = logging.Formatter(
            log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Консольный handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Файловый handler
        log_file = log_config.get('file')
        if log_file:
            # Создаем директорию для логов если нужно
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _setup_device(self) -> bool:
        """
        Настройка подключения к устройству
        
        Returns:
            bool: True если подключение успешно
        """
        try:
            device_config = self.config['device']
            
            self.logger.info(f"Подключение к устройству через {device_config['interface']}...")
            
            self.device = create_device_client(device_config)
            return self.device.connect()
            
        except ConnectionError as e:
            self.logger.error(f"Ошибка подключения: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Неожиданная ошибка: {e}")
            return False
    
    def _log_reading(self, reading: Dict[str, Any]) -> None:
        """
        Запись показаний в лог файл
        
        Args:
            reading: Показания устройства
        """
        log_config = self.config['monitoring']
        log_file = log_config.get('log_file', 'device_readings.log')
        
        try:
            # Создаем директорию если нужно
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # Проверяем размер файла (ротация)
            if os.path.exists(log_file):
                file_size_mb = os.path.getsize(log_file) / (1024 * 1024)
                if file_size_mb > log_config.get('max_log_size_mb', 10):
                    self._rotate_log_file(log_file, log_config.get('max_log_files', 5))
            
            # Читаем существующие данные
            data = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            data = json.loads(content)
                            if not isinstance(data, list):
                                # Если файл не список, создаём новый
                                data = [data] if content else []
                except json.JSONDecodeError:
                    # Если JSON сломан, начинаем заново
                    data = []
            
            # Добавляем новую запись
            data.append(reading)
            
            # Записываем ВЕСЬ список обратно
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Записаны показания в {log_file}, всего записей: {len(data)}")
            
        except Exception as e:
            self.logger.error(f"Ошибка записи в лог: {e}")
    
    def _rotate_log_file(self, log_file: str, max_files: int) -> None:
        """
        Ротация лог файлов
        
        Args:
            log_file: Путь к основному лог файлу
            max_files: Максимальное количество файлов
        """
        try:
            # Удаляем самый старый файл если превышен лимит
            for i in range(max_files - 1, 0, -1):
                old_file = f"{log_file}.{i}"
                if os.path.exists(old_file):
                    if i == max_files - 1:
                        os.remove(old_file)  # Удаляем самый старый
                    else:
                        os.rename(old_file, f"{log_file}.{i+1}")
            
            # Переименовываем текущий файл
            if os.path.exists(log_file):
                os.rename(log_file, f"{log_file}.1")
                
        except Exception as e:
            self.logger.error(f"Ошибка ротации лог файла: {e}")
    
    def _signal_handler(self, signum, frame):
        """
        Обработчик сигналов для graceful shutdown
        """
        self.logger.info(f"Получен сигнал {signum}, остановка...")
        self.is_running = False
    
    def run(self) -> None:
        """
        Основной цикл мониторинга
        """
        if not self._setup_device():
            self.logger.error("Не удалось подключиться к устройству. Выход.")
            return
        
        self.is_running = True
        period = self.config['monitoring'].get('period', 2.0)
        
        self.logger.info(f"Запуск мониторинга с периодом {period} секунд")
        
        try:
            while self.is_running:
                cycle_start = time.time()
                
                try:
                    # Получаем показания
                    reading = self.device.get_reading()
                    
                    # Конвертируем в словарь для JSON
                    reading_dict = reading.to_dict()
                    
                    # Записываем в лог
                    self._log_reading(reading_dict)
                    
                    # Логируем в консоль (только если не ERROR)
                    if reading.status == "OK":
                        self.logger.info(
                            f"Показания: {reading.voltage}, {reading.current}, "
                            f"SN: {reading.serial}"
                        )
                    else:
                        self.logger.warning(
                            f"Ошибка: {reading.error} | "
                            f"Показания: {reading.voltage}, {reading.current}"
                        )
                        
                except ConnectionError as e:
                    self.logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: Потеряно соединение с устройством: {e}")
                    self.logger.error("Завершение работы согласно требованиям спецификации")
                    break  # Выходим из цикла while (немедленное завершение)
                        
                except Exception as e:
                    self.logger.error(f"Ошибка в цикле мониторинга: {e}")
                
                # Вычисляем время до следующего цикла
                cycle_time = time.time() - cycle_start
                sleep_time = max(0.1, period - cycle_time)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Очистка ресурсов"""
        self.logger.info("Очистка ресурсов...")
        
        if self.device:
            try:
                self.device.disconnect()
            except:
                pass
        
        self.logger.info("Монитор остановлен")


def main():
    """Точка входа"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Монитор устройства")
    parser.add_argument("--config", help="Путь к конфигурационному файлу")
    parser.add_argument("--test", action="store_true", help="Тестовый режим (один запрос)")
    parser.add_argument("--daemon", action="store_true", help="Запуск в режиме демона")
    
    args = parser.parse_args()
    
    # Настройка демонизации
    if args.daemon:
        # Стандартный способ демонизации в Python
        import daemon
        from daemon.pidfile import TimeoutPIDLockFile
        
        pid_file = "/var/run/device_monitor.pid"
        
        context = daemon.DaemonContext(
            pidfile=TimeoutPIDLockFile(pid_file),
            stdout=sys.stdout,
            stderr=sys.stderr,
            detach_process=True,
        )
        
        with context:
            monitor = DeviceMonitor(args.config)
            monitor.run()
    else:
        monitor = DeviceMonitor(args.config)
        
        if args.test:
            # Тестовый режим - один запрос
            try:
                if monitor._setup_device():
                    reading = monitor.device.get_reading()
                    print(json.dumps(reading.to_dict(), indent=2))
                    monitor.device.disconnect()
            except Exception as e:
                print(f"Ошибка: {e}")
        else:
            # Нормальный режим
            monitor.run()


if __name__ == "__main__":
    main()