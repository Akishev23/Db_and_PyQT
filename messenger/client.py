"""
client's part of messager
"""
# -*- coding: utf-8 -*-
import json
import time
import socket
import sys
import threading
from library.functions import listen_and_get, decode_and_send, say_hello, args_parser
from library.variables import MESSAGE, MESSAGE_TEXT, TIME, ACTION, SENDER, ERROR, \
    RESPONSE, EXIT, RECEIVER, DEFAULT_PORT
from library.errors import ServerError
from library.metalasses import ClientVerifier
from library.descriptors import IpValidation, ApprovedPort
from decor import logger, log


class Client(metaclass=ClientVerifier):
    address = IpValidation()
    port = ApprovedPort()

    def __init__(self, addr: str, current_port: int, nickname: str):
        self.address = addr
        self.port = current_port
        self.name = nickname
        self.socket_transport = None

    def establish_connection(self):
        """
        establish a connection to the server
        :return:
        """
        self.socket_transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_transport.connect((self.address, self.port))
        logger.info(f'client with keys {self.address} - {self.port} - {self.name} '
                    f'launched')

    @log
    def read_message(self, message: dict):
        """
        reading messages dictionary
        :param message: dictionary
        :return: nothing
        """
        message_key = [ACTION, SENDER, MESSAGE_TEXT]

        if message and RESPONSE in message:
            if message.get(RESPONSE) == 200:
                return '200 : ok'
            raise ServerError(f'{message[ERROR]}')

        if all(message.get(key) for key in message_key) and message.get('action') == MESSAGE:
            logger.info(f'got message {message[SENDER]}' "\n"
                        f'--------------------------------------------'
                        f'{message[MESSAGE_TEXT]}')
            print(message.get(MESSAGE_TEXT))
            return
        else:
            logger.info(f'wrong format of the message'
                        f'{message}')
            return

    @log
    def form_message(self):
        """
        making message before sending it
        :return: message dictionary
        """
        receiver = input('Input to whom message is addressed \n')
        message = input('input message \n')
        ms_ready = {
            ACTION: MESSAGE,
            SENDER: self.name,
            RECEIVER: receiver,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.info('message processed')
        try:
            decode_and_send(self.socket_transport, ms_ready)
            logger.info(f'message for {receiver} from {self.name} has been successfully sent')
        except Exception:
            logger.exception('exception')
            sys.exit(1)

    @log
    def create_exit_message(self):
        """
        creating exit notification
        :return: None
        """
        return {
            ACTION: EXIT,
            TIME: time.time(),
            SENDER: self.name
        }

    @log
    def create_who_is_online_message(self):
        """
        functions for providing who is online info
        :return:
        """
        who_is_online_dictionary = {
            ACTION: 'WHO_ONLINE',
            TIME: time.time(),
            SENDER: self.name
        }
        try:
            decode_and_send(self.socket_transport, who_is_online_dictionary)
            logger.info('List of online clients has been acquired')
        except Exception:
            logger.exception('cannot send who is online message')

    @log
    def getting_message_from_server(self):
        """
        function which handles the messages from server
        :param sock: socket object
        :param name: str
        :return: None
        """
        while True:
            try:
                msg = listen_and_get(self.socket_transport)
                check_dict = [ACTION, SENDER, RECEIVER, MESSAGE_TEXT]
                if all(msg.get(key) for key in check_dict) and msg[ACTION] == 'message' and \
                        msg[RECEIVER] == self.name:
                    print(f'Message from user {msg[SENDER]}: \n'
                          f'\n {msg[MESSAGE_TEXT]}')
                else:
                    logger.error(f'Wrong format of message from server: {msg}')
            except Exception:
                logger.exception('exception, see further')

    @log
    def get_help(self):
        """
        prints info about all commands which are possible to process
        :return:
        """
        print('Possible commands')
        print('message or ms - type your message')
        print('help or h - print help')
        print('exit or ex - exit')
        # print('name - change your nickname') make later
        print('whoisonline or who - who is online')

    @log
    def user_helper(self):
        """
        function - user's interface
        :return: None
        """
        self.get_help()
        while True:
            command = input('Input command: \n')
            if command in ('message', 'ms'):
                self.form_message()
            elif command in ('help', 'h'):
                self.get_help()
            elif command in ('exit', 'ex'):
                decode_and_send(self.socket_transport, self.create_exit_message())
                print('connection is closed')
                logger.info('connection is closed according to users command')
                time.sleep(0.5)
                break
            elif command in ('whoisonline', 'who'):
                logger.info('processed who is online')
                self.create_who_is_online_message()
            else:
                print('Could not recognize command')

    @log
    def main_loop(self):
        """
        client's part of the program
        :return: nothing
        """
        print('Messenger')

        if not self.name:
            self.name = input('input your name')
        print(f'Your nickname is: {self.name}')

        self.establish_connection()

        try:
            greeting = say_hello(self.name)
            decode_and_send(self.socket_transport, greeting)
            listened = listen_and_get(self.socket_transport)
            answer = self.read_message(listened)
            logger.info(f'got server"s approve, {answer}')
            print(f'got server"s approve, {answer}')
        except json.JSONDecodeError:
            logger.error('Unable to decode the message')
            sys.exit(1)
        except ServerError as error:
            logger.error(f'Error of the server, {error}')
        except (ConnectionRefusedError, ConnectionError):
            logger.error('Connection has been refused')
            sys.exit(1)
        else:
            print('Messager')
            print(f'Your start nickname is: {self.name}')

            rec = threading.Thread(target=self.getting_message_from_server,
                                   args=(),
                                   daemon=True)
            rec.start()
            user_int = threading.Thread(target=self.user_helper,
                                        args=(),
                                        daemon=True)
            user_int.start()
            logger.info('all processed are launched')

            while True:
                time.sleep(0.5)
                if rec.is_alive() and user_int.is_alive():
                    continue
                break

    @staticmethod
    def clt_start():
        address, port, nick = args_parser()
        client = Client(address, port, nick)
        client.main_loop()


if __name__ == '__main__':
    Client.clt_start()
