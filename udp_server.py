#!/usr/bin/env python3.10
"""
Простой UDP сервер, эмулирующий устройство LNS.
Отвечает на команды: GET_V, GET_A, GET_S
"""

import socket
import time
import logging
from typing import Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [UDP Device] - %(levelname)s - %(message)s'
)
logger = logging.getLogger('LNSDeviceEmulator')

class LNSDeviceServer:
    """UDP сервер, эмулирующий устройство LNS"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 10000):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        
        # Статические ответы устройства (можно сделать случайными)
        self.responses = {
            'GET_V': 'V_12V',
            'GET_A': 'A_1A', 
            'GET_S': 'S_DSA123'
        }
        
        logger.info(f"Инициализирован эмулятор устройства на {host}:{port}")
    
    def handle_command(self, command: str) -> str:
        """Обработка команд устройства"""
        command = command.strip().upper()
        
        if command in self.responses:
            response = self.responses[command]
            logger.debug(f"Получена команда: {command} -> Ответ: {response}")
            return response
        else:
            logger.warning(f"Неизвестная команда: {command}")
            return "ERROR: Unknown command"
    
    def start(self):
        """Запуск сервера"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.socket.settimeout(1.0)  # Таймаут для graceful shutdown
            self.running = True
            
            logger.info(f"Сервер запущен на {self.host}:{self.port}")
            logger.info("Ожидание команд: GET_V, GET_A, GET_S")
            print(f"=== LNS Device Emulator ===")
            print(f"Listening on: {self.host}:{self.port}")
            print("Commands supported: GET_V, GET_A, GET_S")
            print("=" * 30)
            
            while self.running:
                try:
                    # Получаем данные
                    data, addr = self.socket.recvfrom(1024)
                    
                    # Декодируем команду
                    command = data.decode('utf-8', errors='ignore')
                    
                    # Логируем входящий запрос
                    logger.info(f"Получено от {addr[0]}:{addr[1]}: {command}")
                    
                    # Обрабатываем команду
                    response = self.handle_command(command)
                    
                    # Отправляем ответ
                    self.socket.sendto(response.encode('utf-8'), addr)
                    
                    # Логируем исходящий ответ
                    logger.debug(f"Отправлено {addr[0]}:{addr[1]}: {response}")
                    
                    # Выводим в консоль для наглядности
                    print(f"[{time.strftime('%H:%M:%S')}] {addr[0]}:{addr[1]} -> {command} -> {response}")
                    
                except socket.timeout:
                    continue  # Просто проверяем running
                except Exception as e:
                    if self.running:
                        logger.error(f"Ошибка обработки: {e}")
                    
        except Exception as e:
            logger.error(f"Ошибка запуска сервера: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self):
        """Остановка сервера"""
        self.running = False
        if self.socket:
            self.socket.close()
            logger.info("Сервер остановлен")


def main():
    """Точка входа"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LNS Device UDP Emulator')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind')
    parser.add_argument('--port', type=int, default=10000, help='Port to listen')
    
    args = parser.parse_args()
    
    server = LNSDeviceServer(host=args.host, port=args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nСервер остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())