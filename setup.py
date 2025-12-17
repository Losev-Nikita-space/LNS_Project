#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="device-monitor",
    version="1.0.0",
    description="Device monitoring service for UDP/Serial devices",
    author="Nikita_Losev",
    packages=find_packages(include=['device*']),
    
    # Включаем остальные файлы
    package_data={
        'device': ['*.py'],
    },
    
    # Включаем скрипты
    scripts=['scripts/device_monitor.py', 'udp_server.py',],
  
    install_requires=[
        'pyserial>=3.5',    
        'pyyaml>=6.0',
    ],
    
    entry_points={
        'console_scripts': [
            'device-monitor=scripts.device_monitor:main',  
        ],
    },
    
    python_requires='>=3.8',
    
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    include_package_data=True,
)