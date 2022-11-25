"""
useful variables for all the project
"""

DEFAULT_PORT = 7777
DEFAULT_IP_ADDRESS = '127.0.0.1'
MAX_CONNECTIONS = 5
MAX_PACKAGE_LENGTH = 1024
ENCODING = 'utf-8'
ADDING_CONTACT = 'add_contact'
GET_CONTACTS = 'get_contacts'
REMOVE_CONTACT = 'remove_contact'
USERS_REQUEST = 'users_request'
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'sender'
EXIT = 'exit'
RECEIVER = 'receiver'
DATABASE = 'sqlite:///server_db.db3'
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'message_text'
NEW_NAME = ''
RESPONSE_200 = {RESPONSE: 200}
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}
RESPONSE_202 = {RESPONSE: 202,
                MESSAGE_TEXT: None
                }
