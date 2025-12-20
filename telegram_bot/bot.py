#!/usr/bin/env python3.10
"""
Telegram бот для мониторинга устройства

Команды:
/start - Приветствие
/help - Помощь по командам
/status - Проверить статус устройства
/info - Информация о конфигурации
/logs - Последние записи из лога (только для админов)
/restart - Перезапуск сервиса (только для админов)
"""

import sys
import os
import logging
from typing import List, Optional
import json
from datetime import datetime

# Настройка пути для импорта
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

# Наши модули
from telegram_bot.config import BOT_TOKEN, ADMIN_IDS, DEVICE_CONFIG_PATH
from telegram_bot.device_checker import DeviceChecker

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы для ConversationHandler 
CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

class LNSBot:
    """Основной класс Telegram бота"""
    
    def __init__(self, token: str, admin_ids: List[int], config_path: str = None):
        """
        Инициализация бота
        
        Args:
            token: Токен бота от @BotFather
            admin_ids: Список ID администраторов
            config_path: Путь к конфигурации устройства
        """
        self.token = token
        self.admin_ids = admin_ids
        self.config_path = config_path or DEVICE_CONFIG_PATH
        self.device_checker = DeviceChecker(config_path)
        self.application = None
        
        logger.info(f"Бот инициализирован для {len(admin_ids)} админов")
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in self.admin_ids
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        user_id = user.id
        
        welcome_text = (
            f"👋 Привет, {user.first_name}!\n\n"
            f"Я бот для мониторинга устройства LNS_Project.\n\n"
            f"📋 Доступные команды:\n"
            f"/start - Приветственное сообщение\n"
            f"/help - Помощь по командам\n"
            f"/status - Проверить статус устройства\n"
            f"/info - Информация о конфигурации\n"
        )
        
        # Добавляем админские команды если пользователь админ
        if self.is_admin(user_id):
            welcome_text += (
                f"\n👑 Админ-команды:\n"
                f"/logs - Последние записи из лога\n"
                f"/restart - Перезапуск сервиса\n"
            )
        
        await update.message.reply_text(welcome_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        user_id = update.effective_user.id
        
        help_text = (
            "🆘 Помощь по командам:\n\n"
            "Основные команды:\n"
            "• /status - Проверить текущий статус устройства\n"
            "• /info - Показать конфигурацию устройства\n"
            "• /help - Эта справка\n\n"
            "Команда /status выполняет реальный запрос к устройству "
            "и возвращает актуальные показания (напряжение, ток, серийный номер)."
        )
        
        if self.is_admin(user_id):
            help_text += (
                "\n\nАдминские команды:\n"
                "• /logs - Показать последние 5 записей из лога\n"
                "• /restart - Перезапустить сервис мониторинга\n"
            )
        
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status - проверка устройства"""
        await update.message.reply_text("🔍 Проверяю устройство...")
        
        try:
            # Выполняем проверку устройства
            success, message, data = self.device_checker.check_device_status()
            
            # Отправляем результат
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Логируем запрос
            user = update.effective_user
            logger.info(f"Статус запрошен пользователем {user.username} ({user.id}): {success}")
            
        except Exception as e:
            error_msg = f"❌ Ошибка при проверке устройства: {str(e)}"
            logger.error(error_msg)
            await update.message.reply_text(error_msg)
    
    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /info - информация о конфигурации"""
        try:
            info = self.device_checker.get_device_info()
            await update.message.reply_text(info)
        except Exception as e:
            error_msg = f"❌ Ошибка получения информации: {str(e)}"
            logger.error(error_msg)
            await update.message.reply_text(error_msg)
    
    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /logs - просмотр логов (только для админов)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("⛔ У вас нет прав для просмотра логов")
            return
        
        try:
            log_file = "/var/log/lns_project/device_data.json"
            
            if not os.path.exists(log_file):
                await update.message.reply_text("📁 Лог файл не найден")
                return
            
            # Читаем последние записи
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                await update.message.reply_text("📭 Лог файл пуст")
                return
            
            # Берем последние 5 записей
            recent_logs = data[-5:]
            
            response_lines = ["📊 Последние 5 записей из лога:"]
            
            for i, log in enumerate(recent_logs, 1):
                timestamp = log.get('timestamp', 'N/A')
                voltage = log.get('voltage', 'N/A')
                current = log.get('current', 'N/A')
                status = log.get('status', 'N/A')
                
                response_lines.append(
                    f"\n{i}. {timestamp}\n"
                    f"   Статус: {status}\n"
                    f"   Напряжение: {voltage}\n"
                    f"   Ток: {current}"
                )
            
            response = "\n".join(response_lines)
            
            # Разбиваем на части если сообщение слишком длинное
            if len(response) > 4000:
                chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
                for chunk in chunks:
                    await update.message.reply_text(chunk)
            else:
                await update.message.reply_text(response)
                
        except Exception as e:
            error_msg = f"❌ Ошибка чтения логов: {str(e)}"
            logger.error(error_msg)
            await update.message.reply_text(error_msg)
    
    async def restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /restart - перезапуск сервиса (только для админов)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("⛔ У вас нет прав для перезапуска сервиса")
            return
        
        await update.message.reply_text("🔄 Пытаюсь перезапустить сервис...")
        
        try:
            import subprocess
            
            # Пробуем перезапустить сервис
            result = subprocess.run(
                ['sudo', 'systemctl', 'restart', 'lns_project'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                await update.message.reply_text("✅ Сервис успешно перезапущен")
                logger.info(f"Сервис перезапущен по запросу пользователя {user_id}")
            else:
                error_msg = f"❌ Ошибка перезапуска:\n{result.stderr}"
                await update.message.reply_text(error_msg)
                logger.error(error_msg)
                
        except Exception as e:
            error_msg = f"❌ Исключение при перезапуске: {str(e)}"
            await update.message.reply_text(error_msg)
            logger.error(error_msg)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        text = update.message.text.lower()
        
        if any(word in text for word in ['привет', 'hello', 'hi']):
            await update.message.reply_text(f"Привет! Используй /help для списка команд")
        elif any(word in text for word in ['статус', 'status', 'как дела']):
            # Если пользователь пишет "статус" вместо команды
            await self.status_command(update, context)
        else:
            await update.message.reply_text(
                "Я не понимаю текстовые сообщения. Используй команды:\n"
                "/help - для списка команд\n"
                "/status - для проверки устройства"
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Ошибка при обработке обновления: {context.error}")
        
        try:
            # Пытаемся отправить сообщение об ошибке админу
            for admin_id in self.admin_ids:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"⚠️ Ошибка бота: {context.error}"
                )
        except:
            pass
    
    def setup_handlers(self, application: Application):
        """Настройка обработчиков команд"""
        # Основные команды
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("info", self.info_command))
        
        # Админские команды (с проверкой в обработчике)
        application.add_handler(CommandHandler("logs", self.logs_command))
        application.add_handler(CommandHandler("restart", self.restart_command))
        
        # Обработчик текстовых сообщений
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
        
        # Обработчик ошибок
        application.add_error_handler(self.error_handler)
    
    def run(self):
        """Запуск бота"""
        # Создаем приложение
        self.application = Application.builder().token(self.token).build()
        
        # Настраиваем обработчики
        self.setup_handlers(self.application)
        
        logger.info("Бот запускается...")
        
        # Запускаем бота
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Точка входа для запуска бота"""
    # Проверяем наличие токена
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ОШИБКА: Токен бота не установлен!")
        print("Откройте telegram_bot/config.py и установите токен от @BotFather")
        sys.exit(1)
    
    if not ADMIN_IDS or ADMIN_IDS == [123456789]:
        print("❌ ОШИБКА: ID администратора не установлен!")
        print("Откройте telegram_bot/config.py и установите ваш Telegram ID")
        sys.exit(1)
    
    # Создаем и запускаем бота
    bot = LNSBot(
        token=BOT_TOKEN,
        admin_ids=ADMIN_IDS,
        config_path=DEVICE_CONFIG_PATH
    )
    
    bot.run()


if __name__ == '__main__':
    main()
