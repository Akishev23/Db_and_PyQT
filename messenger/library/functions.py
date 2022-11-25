"""
common functions for both parts of program
"""
# -*- coding: utf-8 -*-
import json
import time
import socket
import os
import sys
import argparse
import portion as p
from decor import logger, log
from .variables import MAX_PACKAGE_LENGTH, ENCODING, ACTION, PRESENCE, TIME, \
    DEFAULT_IP_ADDRESS, DEFAULT_PORT, SENDER, MESSAGE_TEXT


def decode_message(message: dict):
    logger.info(f'message has been decoded {message}')
    return json.dumps(message).encode(ENCODING)


def listen_and_get(client: socket.socket):
    while True:
        incoming_message_raw = client.recv(MAX_PACKAGE_LENGTH).decode(ENCODING)
        if incoming_message_raw:
            incoming_message = json.loads(incoming_message_raw)
            bool_message = incoming_message.get(MESSAGE_TEXT)
            sender = incoming_message.get(SENDER) if bool_message else 'server'
            logger.debug(f'got message from sender @{sender}@ '
                         f'{incoming_message.get(MESSAGE_TEXT) if bool_message else incoming_message}')
            if isinstance(incoming_message, dict):
                return incoming_message


def decode_and_send(this_socket: socket.socket, message: dict):
    outgoing_message = decode_message(message)
    this_socket.send(outgoing_message)
    logger.info('message: %s has been successfully sent', outgoing_message)


def say_hello(account_name):
    resp = {
        ACTION: PRESENCE,
        TIME: time.time(),
        SENDER: account_name
    }
    logger.info(f'made a greeting message {resp}')
    return resp


def check_port(num: int):
    available_ports = p.open(1024, 65535)
    if num not in available_ports:
        return 0
    return 1


def check_server_flag():
    launcher_name = os.path.basename(sys.argv[0]).split('.')[0]
    if launcher_name == 'server':
        return True
    return False


def args_parser():
    """
    reading parameters of command line, adding if necessary
    :return: parameters from command line according to launcher_name
    """
    name = None
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, nargs='?')
    flag = check_server_flag()
    if not flag:
        parser.add_argument('-a', default=DEFAULT_IP_ADDRESS, nargs='?')
        parser.add_argument('-n', default='guest', nargs='?')
    else:
        parser.add_argument('-a', default='', nargs='?')
    all_data = parser.parse_args(sys.argv[1:])
    address = all_data.a
    port = int(all_data.p)
    if not flag:
        name = all_data.n
    if not check_port(port):
        logger.error(f'wrong port: {port}')
        sys.exit(1)
    if not flag:
        return address, port, name
    return address, port
