#!/bin/bash
# Управление сервисом lns_project

SERVICE_NAME="lns_project"

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
        cd /opt/lns_project
        ./venv/bin/python device_monitor.py --test --config /etc/lns_project/config.yaml
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|enable|disable|test}"
        exit 1
        ;;
esac