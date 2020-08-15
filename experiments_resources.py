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

    logging.debug("Starting TCP Server")
    tcp_server = TCPServer(host_, port_)
    logging.debug("TCP Server listen")
    tcp_server.listen()
    logging.debug(" TCP Server done.")

import subprocess
import time
import logging
import os
class NDNExp:
    def peek_start(self):
        subprocess.run(["nfd-start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        subprocess.run(["echo 'Message: HELLO WORLD' | ndnpoke /demo/hello"], shell=True)
        time.sleep(20)
        subprocess.run(["nfd-stop"])

def call_ndn_exp():
    intance_NDNExp = NDNExp()
    intance_NDNExp.peek_start()


class NDN_traffic:
    def traffic_start(self):
        #print("Starting NFD")
        subprocess.run(["sudo nfd -c /usr/local/etc/ndn/NFD_low_CS.conf &> /dev/null &"],shell = True  ,stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        #subprocess.run(["sudo nfd-start &> /dev/null &"],shell = True  ,stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        
        time.sleep(2)
        #TODO O tempo do experimento esta estatico em 10m
        subprocess.run("sleep 3m && sudo nfd-stop &", shell = True)
        print("Starting NDN Traffic Server")
        try:
            subprocess.run(["ndn-traffic-server ndn_conf/ndn-traffic-server.conf >> ndn_requests_output.txt "], shell=True,  stderr = subprocess.DEVNULL)
            logging.info("Waiting... ")

        except:
            print("Finalized by actor")
        finally:
            print("Stopping NFD")
            subprocess.run(["sudo nfd-stop"],shell = True, stderr = subprocess.DEVNULL)
        print("Experiment complete. Check the output logs on the Actor")

def call_ndn_traffic():
    instance_ndn_traffic = NDN_traffic()
    instance_ndn_traffic.traffic_start()