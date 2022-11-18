"""
server's part of the project
"""

import socket
import select
from library.variables import ACTION, RESPONSE, MAX_CONNECTIONS, PRESENCE, TIME, \
    ERROR, MESSAGE_TEXT, MESSAGE, SENDER, RESPONSE_400, RECEIVER, EXIT, NEW_NAME, DATABASE
from library.functions import listen_and_get, decode_and_send, args_parser
from decor import logger, log
from library.descriptors import ApprovedPort, IpValidation
from library.metalasses import ServerVerifier
from database_component import ServerArchive


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

        presence_keys = [ACTION, TIME, SENDER]
        message_keys = [ACTION, TIME, RECEIVER, SENDER, MESSAGE_TEXT]
        who_is_online = [ACTION, TIME, SENDER]
        # change_nickname = [ACTION, TIME, SENDER, NEW_NAME] TODO: change, but i'm not assured
        #  it's necessary
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
        print(f'Поддерживаемые команды:'
              f'users or -u ------ full list of users'
              f'online or -o ------list of online clients'
              f'history or -h ------ history of clients joints and leaves'
              f'quit or -q --- close help instance'
              f'help or -h ----- info about all supported commands')

    def process_help(self):
        """
        function processes help commands for the server instance
        :return:
        """
        self.print_help()
        while True:
            command = input('Input a command')
            if command in ['users', '-u']:
                for user in self.database.all_users():
                    print(user)
            elif command in ['online', '-o']:
                for user in self.database.online_users():
                    print(user)
            elif command in ['history', '-h']:
                user = input('Input username or leave blank to see all users history')
                if not user:
                    user = None
                for row in self.database.get_history(username=user):
                    print(row)
            elif command in ['quit', '-q']:
                break
            else:
                print('unknown command, try again')
                self.print_help()

    @log
    def main_server_algo(self):
        """
        main function of server's part
        :return:
        """
        self.database = ServerArchive(database=self.db_string)
        self.database.create_tables()
        self.socket_starting()
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
                    except Exception:
                        logger.info(f'Connection with {clt.getpeername()} has been lost')
                        self.clients.remove(clt)

            if self.messages:
                for msg in self.messages:
                    try:
                        self.send_message_to_receiver(msg, clients_to_send)
                    except Exception:
                        logger.info(f'Unable to send message to {msg[RECEIVER]}')
                        self.clients.remove(self.names[msg[RECEIVER]])
                        del self.names[msg[RECEIVER]]
                self.messages.clear()

        # self.process_help() TODO: handle that function with treads

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
