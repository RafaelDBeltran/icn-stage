import imp
import socket
import json
from time import sleep
import sys
import paramiko
import logging
from kazoo.client import *
import kazoo
import os
from scp import SCPClient

CONFIG_FILE = "config.json"
JSON_FILE = json.load(open(CONFIG_FILE))
MAX_ATTEMPTS = 100

diretors_list = []
remote_host = None
remote_username = None
remote_password = None
remote_pkey_path = None

for count, i in enumerate(JSON_FILE['Nodes']):
    diretors_list.append(i['remote_hostname'])


def detect_my_role(hp,port=2181):
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    role = None

    sk.connect((hp,port))
    sk.send(b'srvr')
    role = sk.recv(1024)
    role = role.decode('utf-8')
    sk.close()

    if role.find("leader") != -1: 
        return True
    else:
        return False


# port = 8081
# IsRunning = False
leader = None

class RemoteControllICN_stage:
    def __init__(self, config_file = "config.json") -> None:
        self.config_file = config_file
        self.json_file = json.load(open(CONFIG_FILE))

    def send_command(self, command) -> None:                
        try:
            for ip in diretors_list:
                X = detect_my_role(ip)
                # print(X)
                if X:
                    leader = ip
                    break

            for count, i in enumerate(self.json_file['Nodes']):

                if i['remote_hostname'] == leader:
                    remote_host = i['remote_hostname']
                    remote_username = i['remote_username']
                    remote_password = i['remote_password']
                    remote_pkey_path = i['remote_pkey_path']
                    break

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(remote_host, username=remote_username, password=remote_password, pkey=paramiko.RSAKey.from_private_key_file(remote_pkey_path))

            stdin, stdout, stderr = ssh.exec_command('cd icn-stage && sudo python3 icn-stage.py {}'.format(command))

            sleep(5)
            print(stdout.readlines())
            # print(stderr.readlines())


        except:

            for count, i in enumerate(self.json_file['Nodes']):
                remote_host = i['remote_hostname']
                remote_username = i['remote_username']
                remote_password = i['remote_password']
                remote_pkey_path = i['remote_pkey_path']
                break
        
            # print(remote_host)
            # print(remote_username)
            # print(remote_password)
            # print(remote_pkey_path)

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(remote_host, username=remote_username, password=remote_password, pkey=paramiko.RSAKey.from_private_key_file(remote_pkey_path))


            stdin, stdout, stderr = ssh.exec_command('cd icn-stage && sudo python3 icn-stage.py {}'.format(command))

            sleep(5)
            print(stdout.readlines())
            # print(stderr.readlines())
            if command == 'ensemble-start':
                sleep(30)

    def get_busy_actor(self, port = '2181') -> None:
        zk_addr = None
        busy_actor = None
        for ip in diretors_list:
            X = detect_my_role(ip)
            if X:
                zk_addr = ip
                break
        zk_addr = zk_addr + ':' + port
        print("get_source zk_addr: {}".format(zk_addr))
        zk = KazooClient(zk_addr, connection_retry=kazoo.retry.KazooRetry(max_tries=-1, max_delay=250))
        print("zk: {}".format(zk))
        # zk.add_listener(lambda x: os._exit(1) if x == KazooState.LOST else None)
        zk.start()
        

        for actor in zk.get_children('/connected/busy_workers'):
            print("found_actor!: {}".format(actor))
            busy_actor = actor
            # return actor
            

        # count_attempts = 0
        # while count_attempts < MAX_ATTEMPTS:
        #     count_attempts += 1
        #     print("count_attempts: {}".format(count_attempts))
        #     for actor in zk.get_children('/connected/busy_workers'):
        #         print("found_actor!: {}".format(actor))
        #         return actor
        #     sleep(1)
        # zk.close()
        return busy_actor
    
    def send_command_with_parameters(self, command, remote_hostname, remote_username, remote_password, remote_pkey_path) -> None:                
            
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_hostname, username=remote_username, password=remote_password, pkey=paramiko.RSAKey.from_private_key_file(remote_pkey_path))

        stdin, stdout, stderr = ssh.exec_command('{}'.format(command))

        sleep(5)
        print(stdout.readlines())
        print(stderr.readlines())

    def copyfile(self, ip):
        
        busy_actor = ip

        for count, i in enumerate(self.json_file['auxiliars']):
            if i['remote_hostname'] == busy_actor:
                remote_host = i['remote_hostname']
                remote_username = i['remote_username']
                remote_password = i['remote_password']
                remote_pkey_path = i['remote_pkey_path']
                break

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host, username=remote_username, password=remote_password, pkey=paramiko.RSAKey.from_private_key_file(remote_pkey_path))

        with SCPClient(ssh.get_transport()) as scp:
            scp.get('/icn/log.out','/icn/')

    def send_command_to_busy_actor(self, command, ip) -> None:                
                
            # busy_actor = self.get_busy_actor()
            busy_actor = ip

            for count, i in enumerate(self.json_file['workers']):
                if i['remote_hostname'] == busy_actor:
                    remote_host = i['remote_hostname']
                    remote_username = i['remote_username']
                    remote_password = i['remote_password']
                    remote_pkey_path = i['remote_pkey_path']
                    break

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(remote_host, username=remote_username, password=remote_password, pkey=paramiko.RSAKey.from_private_key_file(remote_pkey_path))

            stdin, stdout, stderr = ssh.exec_command('{}'.format(command))

            sleep(5)
            print(stdout.readlines())
            print(stderr.readlines())

    def detect_zookeeper_role(self, hp,port=2181):
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

