"""
the body of logger
"""
# -*- coding: utf-8 -*-

import os
import sys
import logging.config
from all_logging.log_scripts.log_settings import logger_config

logging.config.dictConfig(logger_config)

log_server = logging.getLogger('server')
log_client = logging.getLogger('client')


def main():
    """
    Function only to check if the all_logging algo is correct
    :return: int
    """
    log_server.warning('rest warning')
    log_server.debug('test debug')
    log_server.error('test error')
    try:
        k_test = 1 / 0
        return k_test
    except Exception:
        log_client.exception('Got exception')
        return


if __name__ == '__main__':
    main()
