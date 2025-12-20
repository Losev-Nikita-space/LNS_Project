#!/bin/bash
# Скрипт установки Telegram бота lns_project_bot

set -e

SERVICE_NAME="lns_project_bot"
INSTALL_DIR="/opt/lns_project_bot"

echo "Установка $SERVICE_NAME..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    exit 1
fi

# Создаем директорию
mkdir -p "$INSTALL_DIR"

# Копируем файлы бота
echo "Копирую файлы бота..."
cp config.py bot.py "$INSTALL_DIR/"

# Устанавливаем зависимости
echo "Устанавливаю python-telegram-bot..."
pip3 install python-telegram-bot==20.7

# Создаем systemd сервис
echo "Создаю systemd сервис $SERVICE_NAME..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=LNS Project Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/bot.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

# Обновляем systemd
systemctl daemon-reload

echo ""
echo "=" * 50
echo "✅ Установка завершена!"
echo ""
echo "ПЕРЕД ЗАПУСКОМ отредактируйте настройки:"
echo "  sudo nano $INSTALL_DIR/config.py"
echo ""
echo "Настройте параметры устройства:"
echo "  DEVICE_HOST = 'IP_вашего_устройства'"
echo "  DEVICE_PORT = порт_устройства"
echo ""
echo "Команды управления:"
echo "  sudo systemctl start $SERVICE_NAME     # Запустить"
echo "  sudo systemctl stop $SERVICE_NAME      # Остановить"
echo "  sudo systemctl status $SERVICE_NAME    # Статус"
echo "  sudo journalctl -u $SERVICE_NAME -f    # Логи"
echo ""
echo "Для автоматического запуска при загрузке:"
echo "  sudo systemctl enable $SERVICE_NAME"
echo "=" * 50