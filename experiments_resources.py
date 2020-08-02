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
            print('Connection coming from: ' + str(client_address))
            data = client_socket.recv(25)
            logging.info('Message from client: ' + str(data.decode('UTF-8')))
            print('Message from client: ' + str(data.decode('UTF-8')))

        finally:
            server_socket.close()
            logging.info("Connection closed.")

def call_tcpserver(host_, port_):

    logging.debug("Starting TCP Server")
    tcp_server = TCPServer(host_, port_)
    logging.debug(" TCP Server listen")

    tcp_server.listen()
    logging.debug(" TCP Server done.")

import subprocess
import time
class NDNExp:
    def peek_start(self,ip):
        subprocess.run(["nfd-start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        subprocess.run(["nfdc", "face", "create", "udp://10.0.0.1"])
        time.sleep(5)
        subprocess.run(["nfdc", "route", "add", "/demo/hello", "udp://10.0.0.1"])
        #time.sleep(50)
        for _ in range(0,10):
            time.sleep(0.5)
            subprocess.run(["ndnpeek", "-p", "/demo/hello"])
        subprocess.run(["nfd-stop"])

def call_ndn_exp(ip):
    intance_NDNExp = NDNExp()
    intance_NDNExp.peek_start(ip)