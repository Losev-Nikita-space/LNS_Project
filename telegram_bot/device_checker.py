#!/usr/bin/env python3.10
"""
Модуль для проверки состояния устройства через Telegram бота
"""

import sys
import os
import yaml
from typing import Dict, Any, Tuple
import logging

# Добавляем путь к модулю device
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from device.device_client import create_device_client

logger = logging.getLogger(__name__)

class DeviceChecker:
    """Класс для проверки доступности устройства"""
    
    def __init__(self, config_path: str = None):
        """
        Инициализация проверяльщика устройства
        
        Args:
            config_path: Путь к конфигурационному файлу устройства
        """
        self.config_path = config_path or "/etc/lns_project/config.yaml"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации устройства"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"Файл конфигурации не найден: {self.config_path}")
                # Возвращаем конфиг по умолчанию
                return {
                    'device': {
                        'interface': 'udp',
                        'host': '127.0.0.1',
                        'port': 10000,
                        'timeout': 5.0
                    }
                }
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            return {}
    
    def check_device_status(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Проверка статуса устройства
        
        Returns:
            Tuple[bool, str, Dict]: (успешно, сообщение, данные)
        """
        try:
            if not self.config or 'device' not in self.config:
                return False, "Ошибка конфигурации", {}
            
            device_config = self.config['device']
            
            # Создаем клиент устройства
            device = create_device_client(device_config)
            
            # Пробуем подключиться
            if not device.connect():
                return False, "❌ Не удалось подключиться к устройству", {}
            
            # Получаем показания
            reading = device.get_reading()
            device.disconnect()
            
            # Формируем сообщение
            if reading.status == "OK":
                message = (
                    f"✅ Устройство доступно\n"
                    f"📊 Показания:\n"
                    f"• Напряжение: {reading.voltage}\n"
                    f"• Ток: {reading.current}\n"
                    f"• Серийный номер: {reading.serial}\n"
                    f"• Время: {reading.timestamp}"
                )
                return True, message, reading.to_dict()
            else:
                message = f"⚠️ Устройство ответило с ошибкой: {reading.error}"
                return True, message, reading.to_dict()
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка проверки устройства: {error_msg}")
            
            # Детализируем ошибку для пользователя
            if "Таймаут" in error_msg or "timeout" in error_msg.lower():
                message = "⏱️ Таймаут подключения к устройству"
            elif "Сокет" in error_msg or "socket" in error_msg.lower():
                message = "🔌 Ошибка сетевого подключения"
            elif "Не удалось подключиться" in error_msg:
                message = "🔌 Устройство недоступно"
            else:
                message = f"❌ Ошибка: {error_msg}"
            
            return False, message, {'error': error_msg}
    
    def get_device_info(self) -> str:
        """Получение информации о конфигурации устройства"""
        if not self.config or 'device' not in self.config:
            return "Конфигурация не загружена"
        
        device_config = self.config['device']
        info_lines = ["📋 Конфигурация устройства:"]
        
        for key, value in device_config.items():
            info_lines.append(f"• {key}: {value}")
        
        return "\n".join(info_lines)
