"""1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться
доступность сетевых узлов. Аргументом функции является список, в котором каждый сетевой узел
должен быть представлен именем хоста или ip-адресом. В функции необходимо перебирать ip-адреса и
проверять их доступность с выводом соответствующего сообщения («Узел доступен»,
«Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться с помощью функции
ip_address(). """

import subprocess
import platform
import ipaddress
import socket
import concurrent.futures
from tabulate import tabulate


class HostRange:
    """
    class to keep track of hosts list
    """

    def __init__(self, all_hosts: list):
        self.list_of_hosts = all_hosts
        self._info = []

    def adding_ip_to_hosts(self, current_host: str):
        """
        haldles non-ip hosts
        :param current_host: string
        :return:
        """
        try:
            real_ip = socket.gethostbyname(current_host)
            self._info.append([current_host, real_ip])
        except socket.gaierror:
            print(f'Unknown host {current_host}, removing from host range...')

    def clarify(self):
        """
        builds a list of hosts and real_ip
        :return:
        """
        not_an_ip = []
        for host in self.list_of_hosts:
            try:
                self._info.append([host, ipaddress.ip_address(host)])
            except ValueError:
                not_an_ip.append(host)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(not_an_ip)) as executor:
            executor.map(self.adding_ip_to_hosts, not_an_ip)

    def gel_el_index(self, element):
        """
        gets an index of concrete host into list of hosts
        :param element: string(ip)
        :return: int, index of the element
        """
        for index, value in enumerate(self._info):
            if str(value[1]) == element:
                return index

    def pinger(self, ip_str: str):
        """
        pings address itself
        :param ip_str: string
        :return:
        """
        index = self.gel_el_index(ip_str)
        param = '-n' if platform.system().lower() == 'windows' else '-c'

        command = ['ping', param, '1', ip_str]
        handler = subprocess.call(command, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        if not handler:
            self._info[index].append('alive')
        else:
            self._info[index].append('down')

    def thead_dividing(self):
        """
        divides job to threads
        :return:
        """
        sublist_of_real_ip = [str(k[1]) for k in self._info]
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(sublist_of_real_ip)) as executor:
            executor.map(self.pinger, sublist_of_real_ip)

    def print_info(self):
        """
        provides with result in appropriate view
        :return:
        """
        self.clarify()
        self.thead_dividing()
        print(tabulate(self._info, headers=['host', 'ip', 'result']))


if __name__ == '__main__':
    hosts = HostRange(
        [
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
    )
    hosts.print_info()
