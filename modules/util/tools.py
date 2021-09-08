

import json
import logging
import os
import sys


# class ConfigHelper:
#
#     DEFAULT_CONFIG_FILE = "config.json"
#
#     def __init__(self, config_file_=DEFAULT_CONFIG_FILE):
#
#         if os.path.isfile(config_file_):
#             self.config_data = json.load(open(config_file_))
#             self.adapter = self.config_data["zookeeper_adapter"]
#
#         else:
#             print("Config file not found! Config file name: '%s'" % config_file_)
#             print("You may want to create a config file from the available example: cp %s.example %s" % (ConfigHelper.DEFAULT_CONFIG_FILE, config_file_))
#             sys.exit(-1)
#
#
#     def get_ip_adapter(self):
#         # Como o ip do fibre eh dinamico, essa funcao e necessaria para sempre pegar o ip dinamico para o zookeeper.
#         ni.ifaddresses(self.adapter)
#         return ni.ifaddresses(self.adapter)[ni.AF_INET][0]['addr']
#
#     def create_zookeeper_config_file(self):
#         new_my_config_file = my_config_file.replace('NEW_IP', self.get_ip_adapter())
#         text_file = open("apache-zookeeper-3.6.1/conf/zoo.cfg", "w")
#         text_file.write(new_my_config_file)
#         text_file.close()

#./apache-zookeeper-3.6.1/bin/zkServer.sh start

from pyfiglet import Figlet

class View:
    def __init__(self, title = 'ICN Stage'):
        self.title = title
    def print_view(self):
        f = Figlet(font='slant')
        print (f.renderText(self.title))

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from Crypto.PublicKey import RSA
import tarfile
import os


class Sundry:

    @staticmethod
    def get_pkey(path):
        # with open(path, "rb") as key_file:
        #     private_key = serialization.load_pem_private_key(
        #         key_file.read(),
        #         password=None,
        #         backend=default_backend()
        #     )

        # pem = private_key.private_bytes(
        #     encoding=serialization.Encoding.PEM,
        #     format=serialization.PrivateFormat.TraditionalOpenSSL,
        #     encryption_algorithm=serialization.NoEncryption())
        
        f = open(path,'r')
        pem = RSA.importKey(f.read(),  passphrase='')
        return pem

    @staticmethod
    def compress_dir(input_dir_, output_file_):

        tar_file = tarfile.open(output_file_, "w:gz")
        current_dir = os.getcwd()
        os.chdir(input_dir_)
        for name in os.listdir("."):
            tar_file.add("%s" % (name))
        tar_file.close()
        os.chdir(current_dir)
    @staticmethod
    def get_ensemble_ips(json_file):
        f = open(json_file)
        data = json.load(f)
        JSON_PORT = None
        JSON_ADRESS = ''

        for i in data['Settings']:
            JSON_PORT = i['ClientPort']

        for i in data['Nodes']: 
            JSON_ADRESS += (i['remote_host']+':'+str(JSON_PORT)+',')

        return JSON_ADRESS[:-1]
