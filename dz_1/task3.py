"""
3. Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном
формате (использовать модуль tabulate). Таблица должна состоять из двух колонок и выглядеть примерно
так:
"""
from tabulate import tabulate
from task2 import host_range_ping


def host_range_ping_tab(s_host: str, desired_range: int):
    """
    provides result of hosts' checking with tabulate wiew
    :param s_host: string
    :param desired_range: int
    :return:
    """
    info_to_tabulate = {
        'alive': [],
        'down': []
    }
    hosts_info = host_range_ping(s_host, desired_range, print_result=False)
    for host in hosts_info:
        if host[2] == 'alive':
            info_to_tabulate['alive'].append(host[0])
        else:
            info_to_tabulate['down'].append(host[0])
    print(tabulate(info_to_tabulate, headers='keys'))


if __name__ == '__main__':
    starting_host = input('input starting host: ')
    while True:
        try:
            current_range = int(input('input desired range of addresses: '))
            break
        except ValueError:
            print('Proved incorrect range of hosts, you should specify a numerical value')
    host_range_ping_tab(starting_host, current_range)
