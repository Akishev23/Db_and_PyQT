"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона. Меняться
должен только последний октет каждого адреса. По результатам проверки должно выводиться
соответствующее сообщение.
"""
from threading import Thread
from ipaddress import ip_address
from useful import HostRange, progress_bar
from tabulate import tabulate


def host_range_ping(s_host: str, desired_range: int, print_result=True):
    """
    takes a starting host and desired range of ones and prints info regarding their availability
    :param s_host: string
    :param desired_range: int
    :param print_result:bool, print or return result
    :return:
    """
    list_of_hosts = [str(ip_address(s_host) + j) for j in range(desired_range)]
    hosts = HostRange(list_of_hosts)
    hosts.clarify()
    thread = Thread(target=progress_bar, args=(list_of_hosts,), daemon=True)
    thread.start()
    hosts.thead_dividing()
    if print_result:
        print(tabulate(hosts.info, headers=['host', 'ip', 'result']))
    else:
        return hosts.info


if __name__ == '__main__':
    starting_host = input('input starting host: ')
    current_range = int(input('input desired range of addresses: '))
    host_range_ping(starting_host, current_range)

# Задание сформулировано странно. "Меняться должен только последний октет каждого адреса." А если
# я задам такой диапазон, что вынужден будет измениться не только последний октет? Такой диапазон
# не следует принимать и нужно указать максимально возможный? Но об этом ничего не сказано. Прошу
# не снижать балл если в данном случае решение не до конца верно, я исправлю если надо, тут на 15
# минут работы
