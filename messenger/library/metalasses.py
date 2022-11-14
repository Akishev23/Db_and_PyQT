"""
meta classes that should check attributes prior to initialization
1. Реализовать метакласс ClientVerifier, выполняющий базовую проверку класса «Клиент»
(для некоторых проверок уместно использовать модуль dis):

    отсутствие вызовов accept и listen для сокетов;
    использование сокетов для работы по TCP;
    отсутствие создания сокетов на уровне классов, то есть отсутствие конструкций такого вида:
    class Client: s = socket() ...

2. Реализовать метакласс ServerVerifier, выполняющий базовую проверку класса «Сервер»:

    отсутствие вызовов connect для сокетов;
    использование сокетов для работы по TCP.
"""
# Такой код прямо противоречит принципу dry. Мне это не нравится, я попробовал создать
# суперкласс, отнаследовался от него, но в данном случае этот алгоритм не работает. Прошу на
# уроке осветить этот вопрос, спасибо.

import dis


class ServerVerifier(type):
    """
    Checks if there are no methods like 'connect' and tcp connection method is used whithin the
    server class
    """

    def __init__(cls, clsname, bases, clsdict):
        """
        :param clsname: instance of class for which meta is used
        :param bases: tuple of bases classes
        :param clsdict: dict of methods and attributes linked to this instance
        """
        methods, attributes = [], []
        for func in clsdict:
            try:
                instructions = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for element in instructions:
                    if element.opname == 'LOAD_GLOBAL':
                        if element.argval not in methods:
                            methods.append(element.argval)
                    elif element.opname == 'LOAD_ATTR':
                        if element.argval not in attributes:
                            attributes.append(element.argval)
        if 'connect' in methods:
            raise TypeError("Consider not using the method 'connect'")
        if not ('socket' in methods and 'AF_INET' in attributes):
            raise TypeError('socket has not been started correctly')
        super().__init__(clsname, bases, clsdict)


class ClientVerifier(type):
    """
    checks if all the clients are applying correct methods and sockets
    """

    def __init__(cls, clsname, bases, clsdict):
        """
        :param clsname: instance of class for which meta is used
        :param bases: tuple of bases classes
        :param clsdict: dict of methods and attributes linked to this instance
        """
        methods, attributes = [], []
        for func in clsdict:
            try:
                instructions = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for element in instructions:
                    if element.opname == 'LOAD_GLOBAL':
                        if element.argval not in methods:
                            methods.append(element.argval)
                    elif element.opname == 'LOAD_ATTR':
                        if element.argval not in attributes:
                            attributes.append(element.argval)
        not_accepted_methods = ('accept', 'listen')
        if any(command in methods for command in not_accepted_methods):
            raise TypeError("Consider not using such methods as 'accept' and 'listen'")
        if not ('socket' in methods and 'AF_INET' in attributes):
            raise TypeError('socket has not been started correctly')
        super().__init__(clsname, bases, clsdict)
