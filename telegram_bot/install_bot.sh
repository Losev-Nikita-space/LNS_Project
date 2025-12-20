#!/bin/bash
# Скрипт установки Telegram бота для LNS_Project

set -e

SERVICE_NAME="lns_project_bot"
INSTALL_DIR="/opt/lns_project"
USER="daemon"
GROUP="daemon"

# Проверка прав
if [ "$EUID" -ne 0 ]; then
    echo "Этот скрипт должен запускаться с правами root"
    exit 1
fi

echo "Установка Telegram бота для LNS_Project..."

# 1. Копирование файлов бота
echo "Копирование файлов бота..."
mkdir -p "$INSTALL_DIR/telegram_bot"
cp -r telegram_bot/* "$INSTALL_DIR/telegram_bot/"

# 2. Установка зависимостей для бота
echo "Установка зависимостей для бота..."
cd "$INSTALL_DIR"
source venv/bin/activate
pip install python-telegram-bot

# 3. Настройка конфигурации бота
echo "Настройка конфигурации бота..."
if [ ! -f "$INSTALL_DIR/telegram_bot/config.py" ]; then
    echo "Создание конфигурационного файла..."
    cat > "$INSTALL_DIR/telegram_bot/config.py" << 'EOF'
#!/usr/bin/env python3.10
"""
Конфигурация Telegram бота
"""

# ТОКЕН от @BotFather
BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"

# Ваш Telegram ID (узнать у @userinfobot)
ADMIN_IDS = [ВАШ_ID_ЗДЕСЬ]

# Путь к конфигу устройства (такой же как у основного сервиса)
DEVICE_CONFIG_PATH = "/etc/lns_project/config.yaml"
EOF
fi

echo ""
echo "================================================"
echo "ВАЖНО: Настройте конфигурацию бота!"
echo "1. Откройте файл: $INSTALL_DIR/telegram_bot/config.py"
echo "2. Получите токен у @BotFather в Telegram"
echo "3. Получите ваш ID у @userinfobot в Telegram"
echo "4. Замените значения в config.py"
echo "================================================"
echo ""

# 4. Создание systemd сервиса для бота (опционально)
read -p "Создать systemd сервис для автостарта бота? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Создание systemd сервиса для бота..."
    
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Telegram Bot for LNS Device Monitoring
After=network.target lns_project.service
Wants=lns_project.service

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR
Environment="PYTHONPATH=$INSTALL_DIR"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/telegram_bot/bot.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$SERVICE_NAME

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME.service
    
    echo ""
    echo "Сервис бота создан!"
    echo "Команды управления:"
    echo "  systemctl start $SERVICE_NAME    # Запуск бота"
    echo "  systemctl stop $SERVICE_NAME     # Остановка бота"
    echo "  systemctl status $SERVICE_NAME   # Статус бота"
    echo "  journalctl -u $SERVICE_NAME -f   # Логи бота"
fi

echo ""
echo "Установка завершена!"
echo ""
echo "Для запуска бота вручную:"
echo "  cd $INSTALL_DIR"
echo "  source venv/bin/activate"
echo "  python3.10 telegram_bot/bot.py"
echo ""
