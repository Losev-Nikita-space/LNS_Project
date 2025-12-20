#!/usr/bin/env python3
"""
lns_project_bot - Простой бот для проверки устройства LNS
Только 2 команды:
/start - приветствие
/status - проверить устройство
"""

import socket
import time
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN, DEVICE_HOST, DEVICE_PORT, TIMEOUT

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_device_simple():
    """
    Простейшая проверка устройства через UDP
    Устройство должно отвечать на команды:
    - "GET_V" -> "V_12V" (напряжение)
    - "GET_A" -> "A_1A"  (ток)
    - "GET_S" -> "S_DSA123" (серийный номер)
    """
    try:
        # Создаем UDP сокет
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(TIMEOUT)
        
        # Функция для отправки команды и получения ответа
        def send_command(command):
            sock.sendto(command.encode('utf-8'), (DEVICE_HOST, DEVICE_PORT))
            data, _ = sock.recvfrom(1024)
            return data.decode('utf-8', errors='ignore').strip()
        
        # Получаем все показания
        voltage = send_command("GET_V")
        current = send_command("GET_A")
        serial = send_command("GET_S")
        
        sock.close()
        
        # Формируем сообщение
        message = (
            f"✅ Устройство доступно\n\n"
            f"📊 Показания:\n"
            f"Напряжение: {voltage}\n"
            f"Ток: {current}\n"
            f"Серийный номер: {serial}\n\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        )
        
        return True, message
        
    except socket.timeout:
        return False, f"❌ Устройство не отвечает (таймаут {TIMEOUT} сек)"
    except ConnectionRefusedError:
        return False, "❌ Соединение отклонено устройством"
    except socket.gaierror:
        return False, f"❌ Не удается найти устройство {DEVICE_HOST}:{DEVICE_PORT}"
    except Exception as e:
        return False, f"❌ Ошибка подключения: {str(e)}"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я бот для проверки устройства LNS.\n"
        f"Отправь /status чтобы проверить устройство."
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    # Отправляем сообщение о начале проверки
    await update.message.reply_text("🔍 Проверяю устройство...")
    
    # Выполняем проверку
    success, message = check_device_simple()
    
    # Отправляем результат
    await update.message.reply_text(message)
    
    # Логируем
    user = update.effective_user
    logger.info(f"Проверка от {user.username} ({user.id}): {success}")

def main():
    """Главная функция запуска бота"""
    print("=" * 50)
    print("🚀 Запуск lns_project_bot")
    print(f"📡 Устройство: {DEVICE_HOST}:{DEVICE_PORT}")
    print(f"⏱ Таймаут: {TIMEOUT} сек")
    print("=" * 50)
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", start_command))  # help = start
    
    print("🤖 Бот запущен. Нажмите Ctrl+C для остановки.")
    
    # Запускаем бота
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()