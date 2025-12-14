# device/__init__.py
"""
Пакет для работы с устройством LNS
"""

from .device_client import (
    DeviceClient,
    DeviceConfig,
    DeviceReading,
    InterfaceType,
    create_device_client
)

from .exceptions import (
    DeviceError,
    ConnectionError,
    TimeoutError,
    ProtocolError
)

__all__ = [
    'DeviceClient',
    'DeviceConfig',
    'DeviceReading', 
    'InterfaceType',
    'create_device_client',
    'DeviceError',
    'ConnectionError',
    'TimeoutError',
    'ProtocolError'
]