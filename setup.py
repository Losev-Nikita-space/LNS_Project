#!/usr/bin/env python3.10
from setuptools import setup, find_packages

setup(
    name="lns_project",
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
            'lns_project=scripts.device_monitor:main',  
        ],
    },
    
    python_requires='>=3.10',
    
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
    ],
    include_package_data=True,
)