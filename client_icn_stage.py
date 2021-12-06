import socket
import json
from typing import Tuple

CONFIG_FILE = "config.json"
JSON_FILE = json.load(open(CONFIG_FILE))
diretors_list = []


for count, i in enumerate(JSON_FILE['Nodes']):
    diretors_list.append(i['remote_host'])



class client_icn_stage:
    def __init__(self, host, port):

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))

    
    def send_command(self):
        while True:
            try:
                self.client.send(str.encode(input("Command:> ")))
            except socket.error:
                print("Connection refused. Retrying...")
                continue

    
while True:
    for i in diretors_list:
        print(i)
        try:
            client_icn_stage(i, 8081).send_command()
        except socket.error:
            print("Connection refused. Retrying...")
            continue