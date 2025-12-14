#!/usr/bin/env python3
"""
Основной класс для работы с устройством
Может использоваться через import
"""

import logging
import json
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import time
from datetime import datetime

from .udp_driver import UDPDriver
from .serial_driver import SerialDriver
from .exceptions import DeviceError, ConnectionError

logger = logging.getLogger(__name__)

class InterfaceType(Enum):
    """Тип интерфейса подключения"""
    UDP = "udp"
    SERIAL = "serial"
    COM = "com"  # alias для serial


@dataclass
class DeviceConfig:
    """Конфигурация устройства"""
    interface: InterfaceType = InterfaceType.UDP
    host: str = "127.0.0.1"
    port: int = 10000
    serial_port: str = "ttyACM0"
    baudrate: int = 115200
    timeout: float = 5.0
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'DeviceConfig':
        """Создание конфига из словаря"""
        # Конвертируем строку в InterfaceType
        if 'interface' in config_dict:
            if isinstance(config_dict['interface'], str):
                config_dict['interface'] = InterfaceType(config_dict['interface'].lower())
        
        return cls(**config_dict)


@dataclass
class DeviceReading:
    """Показания устройства"""
    timestamp: str
    voltage: str  # "V_12V"
    current: str  # "A_1A"
    serial: str   # "S_DSA123"
    status: str = "OK"
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Конвертация в JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class DeviceClient:
    """
    Основной клиент для работы с устройством.
    
    Пример использования через import:
        >>> from device.device_client import DeviceClient, DeviceConfig
        >>> 
        >>> # Создаем конфигурацию
        >>> config = DeviceConfig(
        >>>     interface=InterfaceType.UDP,
        >>>     host="127.0.0.1",
        >>>     port=10000
        >>> )
        >>> 
        >>> # Создаем клиент
        >>> device = DeviceClient(config)
        >>> 
        >>> # Подключаемся
        >>> device.connect()
        >>> 
        >>> # Получаем показания
        >>> reading = device.get_reading()
        >>> print(reading.to_json())
        >>> 
        >>> # Отключаемся
        >>> device.disconnect()
    
    Или через контекстный менеджер:
        >>> with DeviceClient(config) as device:
        >>>     reading = device.get_reading()
    """
    
    def __init__(self, config: DeviceConfig):
        """
        Инициализация клиента устройства
        
        Args:
            config: Конфигурация устройства
        """
        self.config = config
        self.driver = None
        self.is_connected = False
        
        logger.info(f"Инициализирован DeviceClient: {config.interface.value}")
        
        # Создаем драйвер в зависимости от типа интерфейса
        if config.interface in [InterfaceType.UDP]:
            self.driver = UDPDriver(
                host=config.host,
                port=config.port,
                timeout=config.timeout
            )
        elif config.interface in [InterfaceType.SERIAL, InterfaceType.COM]:
            self.driver = SerialDriver(
                port=config.serial_port,
                baudrate=config.baudrate
            )
        else:
            raise ValueError(f"Неподдерживаемый интерфейс: {config.interface}")
    
    def connect(self) -> bool:
        """
        Подключение к устройству
        
        Returns:
            bool: True если подключение успешно
            
        Raises:
            ConnectionError: Если не удалось подключиться
        """
        try:
            self.is_connected = self.driver.connect()
            return self.is_connected
        except Exception as e:
            raise ConnectionError(f"Ошибка подключения: {e}")
    
    def disconnect(self):
        """Отключение от устройства"""
        if self.driver and hasattr(self.driver, 'disconnect'):
            self.driver.disconnect()
        self.is_connected = False
        logger.info("Отключено от устройства")
    
    def get_reading(self) -> DeviceReading:
        """
        Получить все показания от устройства
        
        Returns:
            DeviceReading: Объект с показаниями
            
        Raises:
            DeviceError: Если произошла ошибка
        """
        if not self.is_connected:
            raise ConnectionError("Устройство не подключено")
        
        try:
            # Получаем все показания
            voltage = self.driver.get_voltage()
            current = self.driver.get_current()
            serial = self.driver.get_serial()
            
            # Создаем объект показаний
            reading = DeviceReading(
                timestamp=datetime.now().isoformat(),
                voltage=voltage,
                current=current,
                serial=serial,
                status="OK"
            )
            
            logger.debug(f"Получены показания: {reading}")
            return reading
            
        except Exception as e:
            # В случае ошибки возвращаем объект с ошибкой
            logger.error(f"Ошибка при получении показаний: {e}")
            
            return DeviceReading(
                timestamp=datetime.now().isoformat(),
                voltage="V_ERROR",
                current="A_ERROR",
                serial="S_ERROR",
                status="ERROR",
                error=str(e)
            )
    
    def get_voltage(self) -> str:
        """Получить только напряжение"""
        if not self.is_connected:
            raise ConnectionError("Устройство не подключено")
        return self.driver.get_voltage()
    
    def get_current(self) -> str:
        """Получить только ток"""
        if not self.is_connected:
            raise ConnectionError("Устройство не подключено")
        return self.driver.get_current()
    
    def get_serial(self) -> str:
        """Получить только серийный номер"""
        if not self.is_connected:
            raise ConnectionError("Устройство не подключено")
        return self.driver.get_serial()
    
    def test_connection(self) -> bool:
        """
        Тестирование соединения с устройством
        
        Returns:
            bool: True если устройство отвечает
        """
        try:
            if not self.is_connected:
                self.connect()
            
            # Пробуем получить серийный номер
            serial = self.driver.get_serial()
            return serial.startswith("S_")
            
        except Exception as e:
            logger.warning(f"Тест соединения провален: {e}")
            return False
        finally:
            if self.is_connected:
                self.disconnect()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# Функция для удобного импорта
def create_device_client(config_dict: Dict[str, Any]) -> DeviceClient:
    """
    Фабрика для создания DeviceClient из словаря конфигурации
    
    Args:
        config_dict: Словарь с конфигурацией
        
    Returns:
        DeviceClient: Экземпляр клиента устройства
        
    Пример:
        >>> config = {
        >>>     "interface": "udp",
        >>>     "host": "127.0.0.1",
        >>>     "port": 10000
        >>> }
        >>> device = create_device_client(config)
    """
    config = DeviceConfig.from_dict(config_dict)
    return DeviceClient(config)


# Экспорт основных классов и функций
_all__ = [
    'DeviceClient',
    'DeviceConfig', 
    'DeviceReading',
    'InterfaceType',
    'create_device_client'
]