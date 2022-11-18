"""
launcher for convenience to test
"""
import random
# -*- coding: utf-8 -*-
import subprocess

processes = []

names = ['Zoe', 'Ina', 'Irene', 'Camilla', 'Carina', 'Kyra', 'Xenia', 'Lara',
         'Natalia', 'Nina', 'Helga', 'Alexander', 'George', 'Gregory', 'Daniel', 'John',
          'Constantine', 'Leo', 'Max']

while True:
    param = input('Choose the command: q - quit, '
                  's + n  - launch server and n clients(max 10), x - close all the windows: ')

    if 'q' in param:
        break
    if 's' in param:
        n = int(param.strip('s'))
        processes.append(subprocess.Popen('python server.py',
                                          creationflags=subprocess.CREATE_NEW_CONSOLE))
        for name in random.sample(names, n):
            processes.append(subprocess.Popen(f'python client.py -n {name}',
                                              creationflags=subprocess.CREATE_NEW_CONSOLE))

    elif param == 'x':
        while processes:
            p_to_del = processes.pop()
            p_to_del.kill()
