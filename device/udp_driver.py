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
    
    def __init__(self, host: str = "127.0.0.1", port: int = 10000, timeout: float = 5.0):
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
            
        Raises:
            ConnectionError: Если не удалось подключиться
        """
        try:
            # Создаем сокет
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(self.timeout)
            
            # Для UDP подключение тестовое - просто проверяем доступность
            # Устанавливаем флаг подключения перед тестовым запросом
            self.is_connected = True
            
            logger.info(f"Попытка подключения к устройству {self.host}:{self.port}")
            
            # Тестовый запрос для проверки соединения
            # Используем отдельный метод для тестового запроса без проверки is_connected
            try:
                # Отправляем тестовую команду
                self.socket.sendto(b"GET_S", (self.host, self.port))
                
                # Получаем ответ
                data, addr = self.socket.recvfrom(1024)
                test_response = data.decode('utf-8', errors='ignore').strip()
                
                logger.debug(f"Тестовый ответ от устройства: {test_response}")
                
                if test_response and test_response.startswith("S_"):
                    logger.info(f"Успешно подключено к устройству {self.host}:{self.port}")
                    return True
                else:
                    self.is_connected = False
                    logger.error(f"Неверный формат тестового ответа: {test_response}")
                    raise ConnectionError(f"Неверный ответ от устройства: {test_response}")
                    
            except socket.timeout:
                self.is_connected = False
                logger.error(f"Таймаут при тестовом запросе к {self.host}:{self.port}")
                raise ConnectionError(f"Таймаут подключения к {self.host}:{self.port}")
            except Exception as e:
                self.is_connected = False
                logger.error(f"Ошибка при тестовом запросе: {e}")
                raise ConnectionError(f"Ошибка тестового запроса: {e}")
                
        except socket.timeout:
            self.is_connected = False
            logger.error(f"Таймаут создания сокета для {self.host}:{self.port}")
            raise TimeoutError(f"Таймаут подключения к {self.host}:{self.port}")
        except Exception as e:
            self.is_connected = False
            logger.error(f"Ошибка создания сокета: {e}")
            raise ConnectionError(f"Ошибка подключения: {e}")
    
    def _send_command(self, command: str) -> str:
        """
        Отправка команды устройству и получение ответа
        
        Args:
            command: Команда для отправки
            
        Returns:
            str: Ответ от устройства
            
        Raises:
            ConnectionError: Если сокет не инициализирован
            TimeoutError: Если превышен таймаут
            ProtocolError: Если ответ в неверном формате
        """
        if not self.socket:
            raise ConnectionError("Сокет не инициализирован")
        
        if not self.is_connected:
            raise ConnectionError("Устройство не подключено")
        
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
                logger.warning(f"Неверный формат ответа для команды {command}: {response}")
                raise ProtocolError(f"Неверный формат ответа: {response}")
            
            return response
            
        except socket.timeout:
            logger.error(f"Таймаут при выполнении команды: {command}")
            raise TimeoutError(f"Таймаут при выполнении команды: {command}")
        except UnicodeDecodeError:
            logger.error(f"Невозможно декодировать ответ от устройства")
            raise ProtocolError(f"Невозможно декодировать ответ от устройства")
        except Exception as e:
            logger.error(f"Ошибка при отправке команды {command}: {e}")
            # Помечаем соединение как разорванное
            self.is_connected = False
            raise ConnectionError(f"Ошибка связи: {e}")
    
    def _validate_response(self, command: str, response: str) -> bool:
        """
        Валидация ответа от устройства
        
        Args:
            command: Отправленная команда
            response: Полученный ответ
            
        Returns:
            bool: True если ответ валиден
        """
        if not response:
            return False
            
        try:
            # Устройство всегда отвечает в формате:
            # GET_V → V_<значение>
            # GET_A → A_<значение>
            # GET_S → S_<значение>
            
            # Извлекаем префикс из команды: GET_V → V
            parts = command.split('_')
            if len(parts) < 2:
                return False
                
            expected_prefix = parts[1]  # GET_V → V
            
            # Проверяем, что ответ начинается с правильного префикса
            return response.startswith(f"{expected_prefix}_")
            
        except Exception:
            return False
    
    def get_voltage(self) -> str:
        """
        Получить напряжение от устройства
        
        Returns:
            str: Значение напряжения (например, "V_12V")
            
        Raises:
            ConnectionError: Если устройство не подключено
            DeviceError: Если произошла ошибка
        """
        try:
            return self._send_command("GET_V")
        except Exception as e:
            # Преобразуем исключения в DeviceError для единообразия
            from .exceptions import DeviceError
            raise DeviceError(f"Ошибка получения напряжения: {e}")
    
    def get_current(self) -> str:
        """
        Получить ток от устройства
        
        Returns:
            str: Значение тока (например, "A_1A")
            
        Raises:
            ConnectionError: Если устройство не подключено
            DeviceError: Если произошла ошибка
        """
        try:
            return self._send_command("GET_A")
        except Exception as e:
            from .exceptions import DeviceError
            raise DeviceError(f"Ошибка получения тока: {e}")
    
    def get_serial(self) -> str:
        """
        Получить серийный номер устройства
        
        Returns:
            str: Серийный номер (например, "S_DSA123")
            
        Raises:
            ConnectionError: Если устройство не подключено
            DeviceError: Если произошла ошибка
        """
        try:
            return self._send_command("GET_S")
        except Exception as e:
            from .exceptions import DeviceError
            raise DeviceError(f"Ошибка получения серийного номера: {e}")
    
    def disconnect(self):
        """Отключение от устройства"""
        if self.socket:
            try:
                self.socket.close()
                logger.debug(f"Сокет закрыт для {self.host}:{self.port}")
            except Exception as e:
                logger.warning(f"Ошибка при закрытии сокета: {e}")
            finally:
                self.socket = None
        
        self.is_connected = False
        logger.info(f"Отключено от устройства {self.host}:{self.port}")
    
    def __enter__(self):
        """Поддержка контекстного менеджера"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Завершение контекстного менеджера"""
        self.disconnect()
    
    def __del__(self):
        """Деструктор для корректного закрытия соединения"""
        self.disconnect()