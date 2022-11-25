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
    RESPONSE, EXIT, RECEIVER, DEFAULT_PORT, ADDING_CONTACT, ACCOUNT_NAME, GET_CONTACTS, \
    REMOVE_CONTACT, USERS_REQUEST
from library.errors import ServerError
from library.metalasses import ClientVerifier
from library.descriptors import IpValidation, ApprovedPort
from decor import logger, log
from client_db import ClientDatabase

sock_lock = threading.Lock()
database_lock = threading.Lock()


class Client(metaclass=ClientVerifier):
    address = IpValidation()
    port = ApprovedPort()

    def __init__(self, addr: str, current_port: int, nickname: str):
        self.address = addr
        self.port = current_port
        self.name = nickname
        self.socket_transport = None
        self.database = ClientDatabase(nickname)

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

        if not self.database.check_user(receiver):
            logger.error('An attempt to send a message to unknown user')
            return
        ms_ready = {
            ACTION: MESSAGE,
            SENDER: self.name,
            RECEIVER: receiver,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.info('message processed')

        with database_lock:
            self.database.save_message(self.name, receiver, message)
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
        print('contacts or c - who is online')
        print('edit or e - edit your contact list')
        print('history or his - message history')

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
            elif command in ('contacts', 'c'):
                with database_lock:
                    contacts = self.database.get_contacts()
                for contact in contacts:
                    print(contact)
            elif command in ('edit', 'e'):
                self.edit_contacts()

            elif command in ('history', 'his'):
                self.print_history()

            else:
                print('Could not recognize command')

    def print_history(self):
        direction = input('Incoming = in, Outgoing = out, all = press Enter')
        with database_lock:
            if direction == 'in':
                history = self.database.get_history(receiver=self.name)
                for message in history:
                    print(f'\n from {message[0]} at {message[3]} : \n {message[2]}')
            elif direction == 'out':
                history = self.database.get_history(sender=self.name)
                for message in history:
                    print(f'\n to {message[1]} at {message[3]}: \n {message[2]}')
            else:
                history = self.database.get_history()
                for message in history:
                    print(f'\n from {message[0]} to {message[1]} at {message[3]}: \n {message[2]}')

    def add_contact_on_server(self, adding_contact):
        logger.debug(f'Create contact {adding_contact}')
        message = {
            ACTION: ADDING_CONTACT,
            TIME: time.time(),
            SENDER: self.name,
            ACCOUNT_NAME: adding_contact
        }
        decode_and_send(self.socket_transport, message)

    def edit_contacts(self):
        direction = input('to delete input del and add to add contact')
        if direction == 'del':
            deleting_contact = input('input nickname of contact youd like to delete ')
            with database_lock:
                if self.database.check_user(deleting_contact):
                    self.database.del_contact(deleting_contact)
                else:
                    logger.error('Attempted to delete unknown contact')
        elif direction == 'add':
            adding_contact = input('input nickname of contact youd like to add')
            if self.database.check_user(adding_contact):
                with database_lock:
                    self.database.add_contact(adding_contact)
                with sock_lock:
                    try:
                        self.add_contact_on_server(adding_contact)
                    except ServerError:
                        logger.error('Unable to send info to the server')

    def contacts_list_request(self):
        logger.debug(f'Asked contact list for {self.name}')
        message = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            SENDER: self.name
        }
        decode_and_send(self.socket_transport, message)
        answer = listen_and_get(self.socket_transport)
        logger.debug('Received server answer')
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[MESSAGE_TEXT]
        raise ServerError

    def user_list_request(self):
        logger.debug(f'Asked for all known user list for {self.name}')
        message = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            SENDER: self.name
        }
        decode_and_send(self.socket_transport, message)
        answer = listen_and_get(self.socket_transport)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            return answer[MESSAGE_TEXT]
        raise ServerError

    def remove_contact_on_server(self, contact):
        logger.debug(f'Removing contact {contact}')
        message = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            SENDER: self.name,
            ACCOUNT_NAME: contact
        }
        decode_and_send(self.socket_transport, message)

    def filling_db(self):
        try:
            users = self.user_list_request()
        except ServerError:
            logger.error('Unable get info from the server')
        else:
            self.database.add_users(users)
        try:
            contacts = self.contacts_list_request()
        except ServerError:
            logger.error('Unable get info from the server')
        else:
            for contact in contacts:
                self.database.add_contact(contact)

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
            self.filling_db()

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
