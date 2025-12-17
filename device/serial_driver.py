#!/usr/bin/env python3
"""
Serial драйвер для работы с устройством
"""

import logging
import serial
import time
from typing import Optional
from .exceptions import ConnectionError, DeviceError

logger = logging.getLogger(__name__)

class SerialDriver:
    """
    Драйвер для работы с устройством по Serial (COM порт)
    """
    
    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        
        logger.debug(f"Serial драйвер инициализирован: {port}@{baudrate}")
    
    def connect(self) -> bool:
        """Подключение к устройству по Serial"""
        try:
            logger.info(f"Подключение к устройству по Serial: {self.port}@{self.baudrate}")
            
            # Добавляем /dev/ если не указано
            port_path = self.port if self.port.startswith('/dev/') else f"/dev/{self.port}"
            
            self.serial_conn = serial.Serial(
                port=port_path,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # Даем время на инициализацию
            time.sleep(2)
            
            # Очищаем буфер
            if self.serial_conn.in_waiting:
                self.serial_conn.read(self.serial_conn.in_waiting)
            
            self.is_connected = True
            logger.info(f"Успешно подключено к {self.port}")
            return True
            
        except serial.SerialException as e:
            logger.error(f"Ошибка подключения к {self.port}: {e}")
            raise ConnectionError(f"Не удалось подключиться к {self.port}: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при подключении: {e}")
            raise ConnectionError(f"Ошибка подключения: {e}")
    
    def _send_command(self, command: str) -> str:
        """Отправка команды и получение ответа"""
        if not self.is_connected or not self.serial_conn:
            raise ConnectionError("Устройство не подключено")
        
        try:
            # Очищаем буфер перед отправкой
            if self.serial_conn.in_waiting:
                self.serial_conn.read(self.serial_conn.in_waiting)
            
            # Отправляем команду
            cmd_bytes = f"{command}\r\n".encode('utf-8')
            self.serial_conn.write(cmd_bytes)
            self.serial_conn.flush()
            
            logger.debug(f"Отправлена команда: {command}")
            
            # Читаем ответ
            response = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
            
            if not response:
                # Пробуем еще раз
                time.sleep(0.1)
                response = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
            
            logger.debug(f"Получен ответ: {response}")
            return response
            
        except serial.SerialException as e:
            logger.error(f"Ошибка связи с устройством: {e}")
            self.is_connected = False
            raise DeviceError(f"Ошибка связи: {e}")
        except Exception as e:
            logger.error(f"Ошибка при отправке команды {command}: {e}")
            raise DeviceError(f"Ошибка выполнения команды: {e}")
    
    def get_voltage(self) -> str:
        """Запрос напряжения"""
        try:
            response = self._send_command("GET_V")
            # Проверяем формат ответа
            if response.startswith("V_"):
                return response
            else:
                raise DeviceError(f"Неверный формат ответа напряжения: {response}")
        except Exception as e:
            raise DeviceError(f"Ошибка получения напряжения: {e}")
    
    def get_current(self) -> str:
        """Запрос тока"""
        try:
            response = self._send_command("GET_A")
            if response.startswith("A_"):
                return response
            else:
                raise DeviceError(f"Неверный формат ответа тока: {response}")
        except Exception as e:
            raise DeviceError(f"Ошибка получения тока: {e}")
    
    def get_serial(self) -> str:
        """Запрос серийного номера"""
        try:
            response = self._send_command("GET_S")
            if response.startswith("S_"):
                return response
            else:
                raise DeviceError(f"Неверный формат ответа серийного номера: {response}")
        except Exception as e:
            raise DeviceError(f"Ошибка получения серийного номера: {e}")
    
    def get_all_metrics(self) -> dict:
        """Получение всех метрик за один запрос"""
        try:
            voltage = self.get_voltage()
            current = self.get_current()
            serial_num = self.get_serial()
            
            return {
                'voltage': voltage,
                'current': current,
                'serial': serial_num,
                'timestamp': time.time()
            }
        except Exception as e:
            raise DeviceError(f"Ошибка получения метрик: {e}")
    
    def disconnect(self):
        """Отключение от устройства"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                self.is_connected = False
                logger.info(f"Отключено от {self.port}")
            except Exception as e:
                logger.error(f"Ошибка при отключении: {e}")
    
    def __del__(self):
        """Деструктор для корректного закрытия соединения"""
        self.disconnect()