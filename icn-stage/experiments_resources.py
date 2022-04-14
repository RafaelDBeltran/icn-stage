import socket
import logging


class TCPServer:
    def __init__(self, host_, port_):
        self.host = host_
        self.port = port_

    def listen(self):
        # create an INET, STREAMing socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind the socket to a public host, and a well-known port
        server_socket.bind((self.host, self.port))
        # become a server socket
        server_socket.listen(5)

        # accept connections from outside
        (client_socket, client_address) = server_socket.accept()
        try:
            logging.info('Connection coming from: ' + str(client_address))
            data = client_socket.recv(25)
            logging.info('Message from client: ' + str(data.decode('UTF-8')))

        except Exception as e:
            logging.error('Exception: {}'.format(e))

        finally:
            server_socket.close()
            logging.info("Connection closed.")


def call_tcp_server(host_, port_):

    logging.info("\tStarting TCP Server")
    tcp_server = TCPServer(host_, port_)
    logging.info("\tTCP Server listen")
    tcp_server.listen()
    logging.info("\tTCP Server done.")

import subprocess
import time
import logging
import os


def call_ndn_exp(timeout, data_name):
    # subprocess.run(["nfd-start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    cmd_str = "sudo nfd &> /dev/null &"
    # cmd_array = shlex.split(cmd_str)
    logging.info("cmd_str: {}".format(cmd_str))
    subprocess.run([cmd_str], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    cmd_str = "echo 'Message: HELLO WORLD' | ndnpoke --timeout {} {}".format(timeout*1000, data_name) #ms
    logging.info("cmd_str: {}".format(cmd_str))
    proc =  subprocess.run([cmd_str], shell=True)
    logging.info("returncode: {}".format(proc.returncode))
    if proc.returncode == 0:
        return "[OK]"
    else:
        return "[FAIL]"

#     '''
#     ndnpoke https://github.com/named-data/ndn-tools/blob/master/manpages/ndnpoke.rst
# 0: Success
# 1: An unspecified error occurred
# 2: Malformed command line
# 3: No Interests received before the timeout
# 5: Prefix registration failed'''
    #time.sleep(20)
    #cmd_str = "sudo pkill ndn"
    #subprocess.run([cmd_str])


class NDN_traffic:
    def traffic_start(self):
        #print("Starting NFD")
        subprocess.run(["sudo cp ./experiments/test_traffic/low.conf /usr/local/etc/mini-ndn/"],shell = True  ,stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        subprocess.run(["sudo nfd -c /usr/local/etc/ndn/low.conf &> /dev/null &"],shell = True  ,stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        #subprocess.run(["sudo nfd-start &> /dev/null &"],shell = True  ,stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        
        time.sleep(2)
        #TODO O tempo do experimento esta estatico em 10m
        #subprocess.run("sleep 13m && sudo nfd-stop &", shell=True)
        print("Starting NDN Traffic Client")
        try:
            subprocess.run(["sudo rm ndn_requests_output.txt"], shell=True)
            subprocess.run(["ndn-traffic-client ndn_conf/ndn-traffic-server.conf >> ndn_requests_output.txt "], shell=True,  stderr = subprocess.DEVNULL)
            logging.info("Waiting... ")

        except:
            print("Finalized by actor")
        finally:
            print("Stopping NFD")
            subprocess.run(["sudo nfd-stop"], shell=True, stderr=subprocess.DEVNULL)
        print("Experiment complete. Check the output logs on the Actor")

def call_ndn_traffic():
    instance_ndn_traffic = NDN_traffic()
    instance_ndn_traffic.traffic_start()

import threading

class NDN_traffic_server:

    def __init__(self, host_, port_):
        self.host = host_
        self.port = port_

    def listen(self):
        # create an INET, STREAMing socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind the socket to a public host, and a well-known port
        self.server_socket.bind((self.host, self.port))
        # become a server socket
        self.server_socket.listen(5)

        # accept connections from outside
        (self.client_socket, self.client_address) = self.server_socket.accept()
        try:
            logging.info('Connection coming from: ' + str(self.client_address))
            data = self.client_socket.recv(25)
            #t = threading.Thread(target=self.stop_nfd, args=(data.decode('UTF-8'),))
            #t.start()
            if str(data.decode('UTF-8')) == 'start-traffic':
                t = threading.Thread(target=self.stop_nfd, args=())
                #t.setDaemon(True)
                t.start()
                self.start_nfd()
                self.start_traffic()

        except Exception as e:
            logging.error('Exception: {}'.format(e))

        finally:
            subprocess.run(["sudo nfd-stop"], shell=True, stderr=subprocess.DEVNULL)
            self.server_socket.close()
            logging.info("Connection closed.")

    def start_nfd(self):
        subprocess.run(["sudo cp ./experiments/test_traffic/low.conf /usr/local/etc/ndn/"],shell = True  ,stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        subprocess.run(["sudo nfd -c /usr/local/etc/ndn/low.conf &> /dev/null &"],shell = True  ,stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

    def start_traffic(self):
        subprocess.run(["sudo rm ndn_requests_output.txt"], shell=True)
        subprocess.run(["ndn-traffic-server ndn_conf/ndn-traffic-server.conf >> ndn_requests_output.txt "], shell=True,  stderr = subprocess.DEVNULL)

    def stop_nfd(self):
        logging.info('Waiting for stop')
        message_from_client = self.client_socket.recv(25)
        message_from_client = message_from_client.decode('utf-8')
        logging.info('stop response {}'.format(message_from_client))
        #while True:
        if str(message_from_client) == 'stop':
            logging.info('killing the nfd')
            subprocess.run(["sudo nfd-stop"], shell=True, stderr=subprocess.DEVNULL)
            #break

def call_ndn_traffic_server(ip,port):
    instance_ndn_traffic = NDN_traffic_server(ip,port)
    instance_ndn_traffic.listen()