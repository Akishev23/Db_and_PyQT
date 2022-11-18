"""
config of common logger
"""
# -*- coding: utf-8 -*-
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

logger_config = {
    'version': 1,
    'formatters': {
        'std_format': {
            'format': '{asctime} - {levelname} - {name} - {message}',
            'style': '{'
        },
        'file_format': {
            'format': '{asctime} - {name} - {module}:{funcName}:{lineno} - {message}',
            'style': '{'
        }
    },
    'handlers': {
        'console_handler': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'std_format'
        },
        'file_server': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'file_format',
            'filename': 'all_logging/logs/server.log',
            'interval': 1,
            'when': 'midnight',
            'encoding': 'utf-8'
        },
        'file_client': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'file_format',
            'filename': 'all_logging/logs/client.log',
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        'server': {
            'level': 'DEBUG',
            'handlers': ['file_server']
        },
        'client': {
            'level': 'DEBUG',
            'handlers': ['file_client']
        }
    }
}
