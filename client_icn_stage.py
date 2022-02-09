import socket
import json
from time import sleep
import sys
import os

CONFIG_FILE = "config.json"
JSON_FILE = json.load(open(CONFIG_FILE))

diretors_list = []

for count, i in enumerate(JSON_FILE['Nodes']):
    diretors_list.append(i['remote_hostname'])


def detect_zookeeper_role(hp,port=2181):
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    role = None

    sk.connect((hp,port))
    sk.send(b'srvr')
    role = sk.recv(1024)
    role = role.decode('utf-8')

    if role.find("leader") != -1: 
        return True
    else:
        return False


port = 8081
ZookeeperStarted = False
counter = 0


while True:
    leader = None
    if ZookeeperStarted:
        for ip in diretors_list:
            X = detect_zookeeper_role(ip)
            if X:
                leader = ip
                break

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((leader, port))


            client.send(str.encode(input("Command[{}]> ".format(leader))))
            response = client.recv(4096)
            if response.decode('utf-8') == 'reconnect':
                sleep(30)
            else:
                print('\n')
            client.close()
        except:
            pass

    else:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((diretors_list[counter], port))

            command = input("Command[{}]> ".format(diretors_list[counter]))

            if command == 'ensemble-start':
                ZookeeperStarted = True
            client.send(str.encode(command))

            response = client.recv(4096)
            if response.decode('utf-8') == 'reconnect':
                sleep(30)
            else:
                print('\n')
            client.close()
        except:
            if counter == 3:
                counter = 0
            else:
                counter += 1
            pass
