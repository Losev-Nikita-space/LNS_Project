#!/bin/bash
# Скрипт установки сервиса device-monitor для systemd

set -e

# Конфигурация
SERVICE_NAME="device-monitor"
INSTALL_DIR="/opt/device_monitor"
CONFIG_DIR="/etc/device_monitor"
LOG_DIR="/var/log/device_monitor"
USER="nobody"
GROUP="nogroup"

# Проверка прав
if [ "$EUID" -ne 0 ]; then
    echo "Этот скрипт должен запускаться с правами root"
    exit 1
fi

echo "Установка сервиса $SERVICE_NAME..."

# 1. Создание директорий
echo "Создание директорий..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"
chown -R $USER:$GROUP "$LOG_DIR"

# 2. Копирование файлов
echo "Копирование файлов..."
cp -r ../device "$INSTALL_DIR/"
cp device_monitor.py "$INSTALL_DIR/"
cp ../../config/config.yaml "$CONFIG_DIR/config.yaml"

# 3. Создание виртуального окружения и установка зависимостей
echo "Настройка Python окружения..."
cd "$INSTALL_DIR"
python3.10 -m venv venv
source venv/bin/activate
pip install pyyaml

# 4. Создание systemd сервиса
echo "Создание systemd сервиса..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Device Monitoring Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR
Environment="PYTHONPATH=$INSTALL_DIR"
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/device_monitor.py --config $CONFIG_DIR/config.yaml --daemon
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
ReadWritePaths=$LOG_DIR

[Install]
WantedBy=multi-user.target
EOF

# 5. Создание конфигурации logrotate
echo "Настройка logrotate..."
cat > /etc/logrotate.d/$SERVICE_NAME << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 $USER $GROUP
    sharedscripts
    postrotate
        systemctl kill -s USR1 $SERVICE_NAME.service >/dev/null 2>&1 || true
    endscript
}
EOF

# 6. Перезагрузка systemd и запуск сервиса
echo "Настройка systemd..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME.service

echo ""
echo "Установка завершена!"
echo ""
echo "Команды управления:"
echo "  systemctl start $SERVICE_NAME    # Запуск сервиса"
echo "  systemctl stop $SERVICE_NAME     # Остановка сервиса"
echo "  systemctl status $SERVICE_NAME   # Статус сервиса"
echo "  journalctl -u $SERVICE_NAME -f   # Просмотр логов"
echo ""
echo "Конфигурация: $CONFIG_DIR/config.yaml"
echo "Логи: $LOG_DIR/"