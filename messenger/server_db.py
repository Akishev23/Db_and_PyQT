"""
DB module
"""
from datetime import datetime
from pprint import pprint
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, \
    DateTime as DT
from sqlalchemy.orm import mapper, sessionmaker
from decor import logger

class ServerArchive:
    """
    Common class provides db functions
    """

    class Users:

        """
        class describing the table "Users"
        """

        def __init__(self, username):
            self.username = username
            self.last_visited = datetime.now()
            self.user_id = None

    class OnlineUsers:

        """
        class describing the table "OnlineUsers"
        """

        def __init__(self, user_id, ipaddress, port, login_time):
            self.user_id = user_id
            self.ipaddress = ipaddress
            self.port = port
            self.login_time = login_time

    class History:

        """
        class describing the table "History" of joining to chat
        """

        def __init__(self, user_id, date, ipaddress, port):
            self.user_id = user_id
            self.date = date
            self.ipaddress = ipaddress
            self.port = port

    class UsersContacts:
        def __init__(self, user_id, contact_id):
            self.local_id = None
            self.user_id = user_id
            self.contact_id = contact_id

    class UserHistory:
        def __init__(self, user_id):
            self.local_id = None
            self.user_id = user_id
            self.sent = 0
            self.received = 0

    def __init__(self, database: str):
        self.database = database
        if 'sqlite:///' not in self.database:
            self.database = 'sqlite:///' + self.database
        self.engine = create_engine(self.database, echo=False, pool_recycle=7200,
                                    connect_args={"check_same_thread": False})
        self.metadata = MetaData()
        self.session = None

    def create_tables(self):
        """
        creates all the tables and cleans online users table
        :return:
        """
        users_table = Table('Users', self.metadata,
                            Column('user_id', Integer, primary_key=True, autoincrement=True),
                            Column('last_visited', DT),
                            Column('username', String, unique=True)
                            )

        online_users_table = Table('OnlineUsers', self.metadata,
                                   Column('local_id', Integer, primary_key=True,
                                          autoincrement=True),
                                   Column('user_id', ForeignKey('Users.user_id')),
                                   Column('ipaddress', String),
                                   Column('port', Integer),
                                   Column('login_time', DT)
                                   )

        history_table = Table('History', self.metadata,
                              Column('local_id', Integer, primary_key=True,
                                     autoincrement=True),
                              Column('user_id', ForeignKey('Users.user_id')),
                              Column('date', DT),
                              Column('ipaddress', String),
                              Column('port', String)
                              )
        contacts_table = Table('Contacts', self.metadata,
                               Column('local_id', Integer, primary_key=True),
                               Column('user_id', ForeignKey('Users.user_id')),
                               Column('contact_id', ForeignKey('Users.user_id'))
                               )

        users_history_table = Table('UsersHistory', self.metadata,
                                    Column('local_id', Integer, primary_key=True),
                                    Column('user_id', ForeignKey('Users.user_id')),
                                    Column('sent', Integer),
                                    Column('received', Integer)
                                    )

        self.metadata.create_all(self.engine)

        mapper(self.Users, users_table)
        mapper(self.OnlineUsers, online_users_table)
        mapper(self.History, history_table)
        mapper(self.UsersContacts, contacts_table)
        mapper(self.UserHistory, users_history_table)

        session = sessionmaker(bind=self.engine)
        self.session = session()

        self.session.query(self.OnlineUsers).delete()
        self.session.commit()

    def join(self, username: str, ipaddress: str, port: int):

        """
        function which performs records in db, regarding client joining
        :param username: str
        :param ipaddress: str
        :param port: int
        :return:
        """

        info = self.session.query(self.Users).filter_by(username=username)

        if info.count():
            user = info.first()
            user.last_visited = datetime.now()

        else:
            user = self.Users(username)
            self.session.add(user)
            self.session.commit()
            to_add_to_history = self.UserHistory(user.user_id)
            self.session.add(to_add_to_history)

        current_id = user.user_id
        new_online_user = self.OnlineUsers(current_id, ipaddress, port, datetime.now())
        self.session.add(new_online_user)

        new_history = self.History(current_id, datetime.now(), ipaddress, port)
        self.session.add(new_history)

        self.session.commit()

    def leave(self, username: str):
        """
        function which performs db records regarding users leaving chat
        :param username: str
        :return:ServerArchive.Users object
        """
        user = self.session.query(self.Users).filter_by(username=username).first()
        self.session.query(self.OnlineUsers).filter_by(user_id=user.user_id).delete()
        self.session.commit()
        return user

    def all_users(self) -> list:
        """
        function returns all known users
        :return: list of tuples of (str of username, datetime of last_visited)
        """
        info = self.session.query(self.Users.username, self.Users.last_visited)
        return info.all()

    def online_users(self) -> list:
        """
        function returns all users who are online right now
        :return: list of tuples of (int of user_id, str of username, str of ipaddress and
        datetime of current joint time)
        """
        info = self.session.query(self.OnlineUsers.user_id,
                                  self.Users.username,
                                  self.OnlineUsers.ipaddress,
                                  self.OnlineUsers.port,
                                  self.OnlineUsers.login_time).join(self.Users)
        return info.all()

    def get_history(self, username=None) -> list:
        """
        function returns the joints history of specific user if username is provided or of all
        the users in db if not
        :param username: default None, in case of provided should be a str
        :return: list of tuples of (int of user_id, str of username, datetime of related joint,
        str of ip, str of port
        """

        info = self.session.query(self.History.user_id,
                                  self.Users.username,
                                  self.History.date,
                                  self.History.ipaddress,
                                  self.History.port).join(self.Users)
        if not username:
            return info.all()
        return info.filter(self.Users.username == username).all()

    def process_message(self, sender, receiver):
        try:
            sender = self.session.query(self.Users).filter_by(username=sender).first().id
            receiver = self.session.query(self.Users).filter_by(username=receiver).first().id
            sender_row = self.session.query(self.UserHistory).filter_by(user=sender).first()
            sender_row.sent += 1
            recipient_row = self.session.query(self.UserHistory).filter_by(user=receiver).first()
            recipient_row.received += 1

            self.session.commit()
        except AttributeError:
            pass
    def add_contact(self, user, contact):
        user = self.session.query(self.Users).filter_by(username=user).first()
        contact = self.session.query(self.Users).filter_by(username=contact).first()

        if not contact or self.session.query(self.UsersContacts).filter_by(user_id=user.id,
                                                                           contact_id=contact.id).count():
            return
        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):

        user = self.session.query(self.Users).filter_by(username=user).first()
        contact = self.session.query(self.Users).filter_by(username=contact).first()

        if not contact:
            return

        print(self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete())
        self.session.commit()

    def get_contacts(self, username):
        user = self.session.query(self.Users).filter_by(username=username).one()
        query = self.session.query(self.UsersContacts, self.Users.username).filter_by(
            user_id=user.user_id).join(self.Users, self.UsersContacts.contact_id ==
                                     self.Users.user_id)
        return [contact[1] for contact in query.all()]

    def message_history(self):
        query = self.session.query(
            self.Users.username,
            self.Users.last_visited,
            self.UserHistory.sent,
            self.UserHistory.received
        ).join(self.Users)
        return query.all()


if __name__ == '__main__':
    testing_db = ServerArchive(database='sqlite:///for_testing_needs_only.db3')
    testing_db.create_tables()
    testing_db.join('Sergey', '132.23.23.10', 5054)
    testing_db.join('Anna', '123.12.34.11', 7777)
    testing_db.join('Slava', '193.12.14.17', 8888)
    onl = testing_db.online_users()
    testing_db.process_message('Anna', '123456678900')
    print(testing_db.message_history())