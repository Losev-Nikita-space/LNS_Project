#!/usr/bin/env python3
"""
UDP драйвер для работы с устройством
"""

import socket
import time
from typing import Optional, Tuple
import logging
from .exceptions import ConnectionError, TimeoutError, ProtocolError

logger = logging.getLogger(__name__)

class UDPDriver:
    """
    Драйвер для работы с устройством по UDP
    
    Устройство ожидает команды и отвечает на них:
    - Запрос: "GET_V" → Ответ: "V_12V"
    - Запрос: "GET_A" → Ответ: "A_1A"  
    - Запрос: "GET_S" → Ответ: "S_DSA123"
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 10000, 
                 timeout: float = 5.0):
        """
        Инициализация UDP драйвера
        
        Args:
            host: IP адрес устройства
            port: Порт устройства
            timeout: Таймаут операций (секунды)
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        
        logger.debug(f"UDP драйвер инициализирован: {host}:{port}")
    
    def connect(self) -> bool:
        """
        Подключение к устройству
        
        Returns:
            bool: True если подключение успешно
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
            
            # Тестовый запрос для проверки соединения
            test_response = self._send_command("GET_S")
            
            if test_response and test_response.startswith("S_"):
                self.is_connected = True
                logger.info(f"Подключено к устройству {self.host}:{self.port}")
                return True
            else:
                raise ConnectionError(f"Неверный ответ от устройства: {test_response}")
                
        except socket.timeout:
            raise TimeoutError(f"Таймаут подключения к {self.host}:{self.port}")
        except Exception as e:
            raise ConnectionError(f"Ошибка подключения: {e}")
    
    def _send_command(self, command: str) -> str:
        """
        Отправка команды устройству и получение ответа
        
        Args:
            command: Команда для отправки
            
        Returns:
            str: Ответ от устройства
            
        Raises:
            TimeoutError: Если превышен таймаут
            ProtocolError: Если ответ в неверном формате
        """
        if not self.socket:
            raise ConnectionError("Сокет не инициализирован")
        
        try:
            # Отправка команды
            self.socket.sendto(command.encode('utf-8'), (self.host, self.port))
            logger.debug(f"Отправлена команда: {command}")
            
            # Получение ответа
            data, addr = self.socket.recvfrom(1024)
            response = data.decode('utf-8', errors='ignore').strip()
            
            logger.debug(f"Получен ответ: {response} от {addr}")
            
            # Проверка формата ответа
            if not self._validate_response(command, response):
                raise ProtocolError(f"Неверный формат ответа: {response}")
            
            return response
            
        except socket.timeout:
            raise TimeoutError(f"Таймаут при выполнении команды: {command}")
        except UnicodeDecodeError:
            raise ProtocolError(f"Невозможно декодировать ответ от устройства")
    
    def _validate_response(self, command: str, response: str) -> bool:
        """
        Валидация ответа от устройства
        
        Args:
            command: Отправленная команда
            response: Полученный ответ
            
        Returns:
            bool: True если ответ валиден
        """
        # Устройство всегда отвечает в формате:
        # GET_V → V_<значение>
        # GET_A → A_<значение>
        # GET_S → S_<значение>
        
        expected_prefix = command.split('_')[1]  # GET_V → V
        return response.startswith(f"{expected_prefix}_")
    
    def get_voltage(self) -> str:
        """
        Получить напряжение от устройства
        
        Returns:
            str: Значение напряжения (например, "V_12V")
        """
        return self._send_command("GET_V")
    
    def get_current(self) -> str:
        """
        Получить ток от устройства
        
        Returns:
            str: Значение тока (например, "A_1A")
        """
        return self._send_command("GET_A")
    
    def get_serial(self) -> str:
        """
        Получить серийный номер устройства
        
        Returns:
            str: Серийный номер (например, "S_DSA123")
        """
        return self._send_command("GET_S")
    
    def disconnect(self):
        """Отключение от устройства"""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.is_connected = False
        logger.info("Отключено от устройства")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()