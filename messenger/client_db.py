"""
class for handling user's databases
"""

from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime


class ClientDatabase:
    class CelebratedUsers:
        def __init__(self, user: str):
            self.id = None
            self.username = user

    class MessageHistory:
        def __init__(self, sender: str, receiver: str, message: str):
            self.id = None
            self.sender = sender
            self.receiver = receiver
            self.message = message
            self.date = datetime.datetime.now()

    class UserContacts:
        def __init__(self, contact: str):
            self.id = None
            self.name = contact

    def __init__(self, name: str):

        self.database_engine = create_engine(f'sqlite:///client_{name}.db3', echo=False,
                                             pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        users = Table('celebrated_users', self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )

        history = Table('message_history', self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('sender', String),
                        Column('receiver', String),
                        Column('message', Text),
                        Column('date', DateTime)
                        )

        contacts = Table('user_contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('name', String, unique=True)
                         )

        self.metadata.create_all(self.database_engine)

        mapper(self.CelebratedUsers, users)
        mapper(self.MessageHistory, history)
        mapper(self.UserContacts, contacts)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.UserContacts).delete()
        self.session.commit()

    def add_contact(self, contact: str):
        if not self.session.query(self.UserContacts).filter_by(name=contact).count():
            contact_row = self.UserContacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact: str):
        self.session.query(self.UserContacts).filter_by(name=contact).delete()

    def add_users(self, users_list: list):
        self.session.query(self.CelebratedUsers).delete()
        for user in users_list:
            user_row = self.CelebratedUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, sender: str, receiver: str, message: str):
        message_row = self.MessageHistory(sender, receiver, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.UserContacts.name).all()]

    def get_users(self):
        return [user[0] for user in self.session.query(self.CelebratedUsers.username).all()]

    def check_user(self, user: str):
        if self.session.query(self.CelebratedUsers).filter_by(username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact: str):
        if self.session.query(self.UserContacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_history(self, sender=None, receiver=None):
        query = self.session.query(self.MessageHistory)
        if sender:
            query = query.filter_by(sender=sender)
        if receiver:
            query = query.filter_by(receiver=receiver)
        return [(history_row.sender, history_row.receiver, history_row.message, history_row.date)
                for history_row in query.all()]


if __name__ == '__main__':
    test_db = ClientDatabase('Denis')
    for i in ['Anna', 'Vadim', 'Elena']:
        test_db.add_contact(i)
    test_db.add_users(['Sergey', 'Egor', 'Galina', 'Sofia'])
    test_db.save_message('Denis', 'Anna',
                         f'Hello! Im here just to check db working {datetime.datetime.now()}!')
    test_db.save_message('Denis', 'Vadim',
                         f'Hello! Im another message just to check db working'
                         f' {datetime.datetime.now()}!')
    print(test_db.get_contacts())
    print(test_db.get_users())
    print(test_db.check_user('Sergey'))
    print(test_db.check_user('New'))
    print(test_db.get_history('Denis'))
    print(test_db.get_history(receiver='Vadim'))
    test_db.del_contact('Elena')
    print(test_db.get_contacts())
