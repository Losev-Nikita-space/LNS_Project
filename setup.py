#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="device-monitor",
    version="1.0.0",
    description="Device monitoring service for UDP/Serial devices",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        'pyyaml>=6.0',
    ],
    entry_points={
        'console_scripts': [
            'device-monitor=device_monitor.scripts.device_monitor:main',
        ],
    },
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
)