"""1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться
доступность сетевых узлов. Аргументом функции является список, в котором каждый сетевой узел
должен быть представлен именем хоста или ip-адресом. В функции необходимо перебирать ip-адреса и
проверять их доступность с выводом соответствующего сообщения («Узел доступен»,
«Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью функции
ip_address(). """

from hostrange import HostRange
from tabulate import tabulate


def host_ping(list_of_hosts: list) -> list:
    """
    shows the result of availability checking in appropriate view
    :param list_of_hosts: list
    :return:
    """
    hosts = HostRange(list_of_hosts)
    hosts.clarify()
    hosts.thead_dividing()
    print(tabulate(hosts.info, headers=['host', 'ip', 'result']))


if __name__ == '__main__':
    l_hosts = [
        '253.254.64.26',
        '28.138.193.141',
        '78.198.213.198',
        'ya.ru',
        '120.30.63.127',
        '172.203.248.57',
        'gb.ru',
        'eyfeyhdAHYdsh.',
        'google.com',
        '137.90.29.61',
        '19.252.78.168'
    ]
    host_ping(l_hosts)

