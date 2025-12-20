"""
Telegram бот для мониторинга устройства
"""

from .bot import LNSBot, main
from .device_checker import DeviceChecker

__version__ = "1.0.0"
__all__ = ['LNSBot', 'DeviceChecker', 'main']