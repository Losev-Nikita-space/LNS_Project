#!/bin/bash
# Управление сервисом device-monitor

SERVICE_NAME="device-monitor"

case "$1" in
    start)
        systemctl start $SERVICE_NAME
        ;;
    stop)
        systemctl stop $SERVICE_NAME
        ;;
    restart)
        systemctl restart $SERVICE_NAME
        ;;
    status)
        systemctl status $SERVICE_NAME
        ;;
    logs)
        journalctl -u $SERVICE_NAME -f
        ;;
    enable)
        systemctl enable $SERVICE_NAME
        ;;
    disable)
        systemctl disable $SERVICE_NAME
        ;;
    test)
        # Тестовый запуск (без демона)
        cd /opt/device_monitor
        ./venv/bin/python device_monitor.py --test --config /etc/device_monitor/config.yaml
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|enable|disable|test}"
        exit 1
        ;;
esac