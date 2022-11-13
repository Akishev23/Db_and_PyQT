"""
logger-decorator, testing some interesting opportunities.
"""

import os
import sys
import inspect
import logging
from functools import wraps
from all_logging.log_scripts import common_logging

if 'server' in os.path.basename(sys.argv[0]):
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def log(func):
    @wraps(func)
    def write_log(*args, **kwargs):
        result_of_function = func(*args, **kwargs)
        logger.info(f'starting the log of deco'"\n"
                    f'run function {func.__name__} with parameters {args} , {kwargs}  '"\n"
                    f'from module {os.path.basename(sys.argv[0])}'"\n"
                    f'from function {inspect.stack()[1][3]}'"\n",
                    stacklevel=2)

        return result_of_function

    return write_log
