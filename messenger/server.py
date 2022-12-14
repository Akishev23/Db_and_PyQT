"""
server's part of the project
"""
import configparser
import socket
import select
import sys
import os
from threading import Thread
import threading
import argparse
from library.variables import ACTION, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, \
    ERROR, MESSAGE_TEXT, MESSAGE, SENDER, RESPONSE_400, RECEIVER, EXIT, NEW_NAME, DATABASE, \
    GET_CONTACTS, RESPONSE_202, REMOVE_CONTACT, ADDING_CONTACT, USERS_REQUEST
from library.functions import listen_and_get, decode_and_send, args_parser
from decor import logger, log
from library.descriptors import ApprovedPort, IpValidation
from library.metalasses import ServerVerifier
from server_db import ServerArchive
import time
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

NEW_CONNECTION = False
flag_lock = threading.Lock()
GIU_CONNECTION = False


class Server(metaclass=ServerVerifier):
    listen_address = IpValidation()
    listen_port = ApprovedPort()

    def __init__(self, listen_address, listen_port, db_string):
        self.listen_address = listen_address
        self.listen_port = listen_port
        self.clients = []
        self.messages = []
        self.names = {}
        self.socket_transport = None
        self.db_string = db_string
        self.database = None
        self.config = None

    def arg_parser(self, default_port, default_address):
        parser = argparse.ArgumentParser()
        parser.add_argument('-p', default=default_port, type=int, nargs='?')
        parser.add_argument('-a', default=default_address, nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        self.listen_address = namespace.a
        self.listen_port = namespace.p

    def socket_starting(self):  # Я так и не понял, почему нельзя применить этот метод внутри
        # экземпляра класса, поэтому пока оставил так, жду ваших пояснений

        """
        creates socket
        :return:
        """
        logger.info(f'Launching server with parameters port= {self.listen_port}, address ='
                    f' {self.listen_address}')
        self.socket_transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_transport.bind((self.listen_address, self.listen_port))
        self.socket_transport.settimeout(0.2)
        self.socket_transport.listen(MAX_CONNECTIONS)
        logger.info(f'server with mentioned parameters port= {self.listen_port}, '
                    f'address={self.listen_address} has been started successfully')

    @log
    def process_client_message(self, message: dict, client: socket.socket):
        """
        processing client's message
        :param client: socket object
        :param message: dictionary
        :return:
        """
        global NEW_CONNECTION
        presence_keys = [ACTION, TIME, SENDER]
        message_keys = [ACTION, TIME, RECEIVER, SENDER, MESSAGE_TEXT]
        who_is_online = [ACTION, TIME, SENDER]
        exit_keys = [ACTION, SENDER]

        if all(message.get(key) for key in presence_keys) and message[ACTION] == PRESENCE:
            logger.debug(f'got correct message of presence from client {message}')
            name = message[SENDER]
            if name not in self.names:
                try:
                    logger.info('adding client to list of clients')
                    self.names[name] = client
                    ipaddress, port = client.getpeername()
                    self.database.join(name, ipaddress, port)
                    decode_and_send(client, {RESPONSE: 200})
                    with flag_lock:
                        NEW_CONNECTION = True
                except:
                    logger.exception('Something went wrong')
            else:
                resp = RESPONSE_400
                resp[ERROR] = 'Pointed name is busy'
                decode_and_send(client, resp)
                self.clients.remove(client)
                client.close()
            return

        if all(message.get(key) for key in message_keys) and message[ACTION] == MESSAGE:
            self.messages.append(message)
            self.database.process_client_message(message[SENDER], message[RECEIVER])
            logger.debug(f'got correct message from client {message}')
            return

        if all(message.get(key) for key in exit_keys) and message[ACTION] == EXIT:
            clt = self.names[message[SENDER]]
            try:
                self.database.leave(message[SENDER])
                self.clients.remove(clt)
            except:
                logger.exception('Something went wrong')
            clt.close()
            del self.names[message[SENDER]]
            with flag_lock:
                NEW_CONNECTION = True
            return

        if all(message.get(key) for key in who_is_online) and message[ACTION] == 'WHO_ONLINE':
            logger.info('Got message to see who is online')
            message[RECEIVER] = message[SENDER]
            clients = [client[1] for client in self.database.online_users()]
            clients.remove(message[SENDER])
            online = '\n'.join(clients)
            message[SENDER] = 'Server'
            message[ACTION] = MESSAGE
            now_online = 'Now online are: \n' + online
            message[MESSAGE_TEXT] = now_online
            self.messages.append(message)
            return

        if ACTION in message and message[ACTION] == GET_CONTACTS:
            resp = RESPONSE_202
            resp[MESSAGE_TEXT] = self.database.get_contacts(message[SENDER])
            decode_and_send(client, resp)
            return
        if ACTION in message and message[ACTION] == REMOVE_CONTACT:
            resp = RESPONSE_202
            self.database.remove_contact(message[SENDER], message[RECEIVER])
            resp[
                MESSAGE_TEXT] = f'Contact {message[RECEIVER]} is successfully removed from your list of' \
                                f'contacts '
            decode_and_send(client, resp)
            return
        if ACTION in message and message[ACTION] == ADDING_CONTACT:
            resp = RESPONSE_202
            self.database.add_contact(message[SENDER], message[RECEIVER])
            resp[
                MESSAGE_TEXT] = f'Contact {message[RECEIVER]} is successfully added to your list of contacts'
            decode_and_send(client, resp)
            return
        if ACTION in message and message[ACTION] == USERS_REQUEST:
            resp = RESPONSE_202
            resp[MESSAGE_TEXT] = [user[0] for user in self.database.all_users()]
            decode_and_send(client, resp)
            return

        resp = RESPONSE_400
        resp[ERROR] = f'query is wrong {message}'
        logger.error(f'got incorrect message from client {message}')
        decode_and_send(client, resp)
        return

    @log
    def send_message_to_receiver(self, message, receiving_sockets):
        """
        function sends messages to recipients if needed
        :param message: dict
        :param receiving_sockets: list of socket objects
        :return: None
        """
        if message[RECEIVER] in self.names and self.names[message[RECEIVER]] in receiving_sockets:
            decode_and_send(self.names[message[RECEIVER]], message)
            logger.info(f'Sent message to {message[RECEIVER]} from user {message[SENDER]}')
            return
        if (message[RECEIVER] in self.names and self.names[message[RECEIVER]] not in
            receiving_sockets) or message[RECEIVER] not in self.names:
            raise ConnectionError
        logger.error(f'User {message[RECEIVER]} is not registered, or socket not in the list, '
                     f'not able to send that message')

    @log
    def accept_client(self, sock: socket.socket) -> tuple[socket.socket, str]:
        """
        accepting clients
        :param sock: socket object
        :return: tuple of socket object and client ip
        """
        while True:
            client, address = sock.accept()
            logger.info(f'Client with address {address} connected')
            return client, address

    def print_help(self):
        """
        prints all supported commands
        :return:
        """
        print(f'Available commands: \n'
              f'users or -u ------ full list of users \n'
              f'online or -o ------list of online clients \n'
              f'history or -h ------ history of clients joints and leaves \n'
              f'quit or -q --- close help instance \n'
              f'help or -h ----- info about all supported commands \n')

    def process_help(self):
        """
        function processes help commands for the server instance
        :return:
        """
        self.print_help()
        while True:
            command = input('Input a command: \n')
            if command in ['users', '-u']:
                for user in self.database.all_users():
                    print(user)
            elif command in ['online', '-o']:
                for user in self.database.online_users():
                    print(user)
            elif command in ['history', '-h']:
                user = input('Input username or leave blank to see all users history: \n')
                if not user:
                    user = None
                for row in self.database.get_history(username=user):
                    print(row)
            elif command in ['quit', '-q']:
                break
            else:
                print('unknown command, try again')
                self.print_help()

    def handle_messages(self):
        """
        function which handles clients and messages
        :return:
        """
        while True:
            try:
                client, client_address = self.accept_client(self.socket_transport)
            except OSError:
                pass
            else:
                logger.info(f'established connection with address: {client_address}')
                self.clients.append(client)

            clients_to_receive = []
            clients_to_send = []

            if self.clients:
                try:
                    clients_to_receive, clients_to_send, _ = select.select(self.clients,
                                                                           self.clients, [], 0)
                except OSError:
                    pass

            if clients_to_receive:
                for clt in clients_to_receive:
                    try:
                        msg = listen_and_get(clt)
                        self.process_client_message(msg, clt)
                    except Exception as e:
                        logger.exception('Unable to process, see underlying')
                        logger.info(f'Connection with {clt.getpeername()} has been lost')
                        for name in self.names:
                            if self.names[name] == clt:
                                self.database.leave(name)
                                del self.names[name]
                                break
                        self.clients.remove(clt)

            if self.messages:
                for msg in self.messages:
                    try:
                        self.send_message_to_receiver(msg, clients_to_send)
                    except Exception:
                        logger.info(f'Unable to send message to {msg[RECEIVER]}')
                        self.clients.remove(self.names[msg[RECEIVER]])
                        self.database.user_logout(msg[RECEIVER])
                        del self.names[msg[RECEIVER]]

                self.messages.clear()

    @log
    def main_server_algo(self):
        """
        main function of server's part
        :return:
        """
        self.config = configparser.ConfigParser()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.config.read(f"{dir_path}/{'settings.ini'}")
        self.arg_parser(
            self.config['SETTINGS']['Default_port'], self.config['SETTINGS']['Listen_Address'])
        self.database = ServerArchive(database=os.path.join(
                self.config['SETTINGS']['Database_path'],
                self.config['SETTINGS']['Database_file']))
        self.database.create_tables()
        self.socket_starting()
        main = Thread(target=self.handle_messages, args=(), daemon=True)
        main.start()
        server_helper = Thread(target=self.process_help, args=(), daemon=True)
        server_helper.start()

        while True:
            time.sleep(0.5)
            if main.is_alive():  # and user_int.is_alive():
                continue
            break

    def gui_part(self):

        server_app = QApplication(sys.argv)
        main_window = MainWindow()

        main_window.statusBar().showMessage('Server Working')
        main_window.active_clients_table.setModel(gui_create_model(self.database))
        main_window.active_clients_table.resizeColumnsToContents()
        main_window.active_clients_table.resizeRowsToContents()

        def list_update():
            global GIU_CONNECTION
            if GIU_CONNECTION:
                main_window.active_clients_table.setModel(
                    gui_create_model(self.database))
                main_window.active_clients_table.resizeColumnsToContents()
                main_window.active_clients_table.resizeRowsToContents()
                with flag_lock:
                    GIU_CONNECTION = False

        def show_statistics():
            stat_window = HistoryWindow()
            stat_window.history_table.setModel(create_stat_model(self.database))
            stat_window.history_table.resizeColumnsToContents()
            stat_window.history_table.resizeRowsToContents()
            stat_window.show()

        def server_config():
            global config_window
            config_window = ConfigWindow()
            config_window.db_path.insert(self.config['SETTINGS']['Database_path'])
            config_window.db_file.insert(self.config['SETTINGS']['Database_file'])
            config_window.port.insert(self.config['SETTINGS']['Default_port'])
            config_window.ip.insert(self.config['SETTINGS']['Listen_Address'])
            config_window.save_btn.clicked.connect(save_server_config)

        def save_server_config():
            global config_window
            message = QMessageBox()
            self.config['SETTINGS']['Database_path'] = config_window.db_path.text()
            self.config['SETTINGS']['Database_file'] = config_window.db_file.text()
            try:
                port = int(config_window.port.text())
            except ValueError:
                message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
            else:
                self.config['SETTINGS']['Listen_Address'] = config_window.ip.text()
                if 1023 < port < 65536:
                    config['SETTINGS']['Default_port'] = str(port)
                    print(port)
                    with open('server.ini', 'w') as conf:
                        self.config.write(conf)
                        message.information(
                            config_window, 'OK', 'Настройки успешно сохранены!')
                else:
                    message.warning(
                        config_window,
                        'Ошибка',
                        'Порт должен быть от 1024 до 65536')

        timer = QTimer()
        timer.timeout.connect(list_update)
        timer.start(1000)
        main_window.refresh_button.triggered.connect(list_update)
        main_window.show_history_button.triggered.connect(show_statistics)
        main_window.config_btn.triggered.connect(server_config)
        server_app.exec_()

    @staticmethod
    def srv_start():
        """
        method only for convenient launch
        :return:
        """
        la, lp = args_parser()
        server = Server(la, lp, DATABASE)
        server.main_server_algo()


if __name__ == '__main__':
    Server.srv_start()
