#!/usr/bin/env python3.10
"""
Исключения для работы с устройством
"""

class DeviceError(Exception):
    """Базовое исключение устройства"""
    pass

class ConnectionError(DeviceError):
    """Ошибка соединения"""
    pass

class TimeoutError(DeviceError):
    """Таймаут операции"""
    pass

class ProtocolError(DeviceError):
    """Ошибка протокола/формата ответа"""
    pass

class CommandError(DeviceError):
    """Ошибка выполнения команды"""
    pass