#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

#client packeges
import socket
import sys
import logging
import argparse

#ndn packeges
import subprocess
import time

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
#DEFAULT_HOST = socket.gethostname()
DEFAULT_HOST = '192.168.133.1'
DEFAULT_PORT = 10000


class TCPClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        logging.info('Starting the connection to the server {} {} '.format(self.host, self.port))
        try:
            self.socket.connect((self.host, self.port))

        except Exception as e:
            logging.error(e)

    def send_hello_message(self):
        try:
            message = 'start-traffic'
            logging.info('Sending start message: ' + str(message))
            self.socket.sendall(message.encode('UTF-8'))

            time.sleep(2)

            self.ndn_channel()

            subprocess.run(["ndn-traffic-client -c 6200 -i 100 ndn-traffic-client.conf >> ndn_traffic_client_output.txt"],shell = True)

        except Exception as e:
            logging.error(e)

        finally:
            stop = 'stop'
            logging.info('Closing Socket')
            subprocess.run(["sudo nfd-stop"], shell = True)
            self.socket.sendall(stop.encode('UTF-8'))
            self.socket.close()

    def ndn_channel(self):
        subprocess.run(["sudo cp low.conf /usr/local/etc/ndn/"],shell = True)
        time.sleep(2)
        subprocess.run(["sudo nfd -c /usr/local/etc/ndn/low.conf > /dev/null &"],shell = True  ,stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
        subprocess.run(["nfdc", "face", "create", "udp://"+str(self.host)])
        subprocess.run(["nfdc", "route", "add", "/example/", "udp://"+str(self.host)])


def main():

	tcp_client = TCPClient(sys.argv[1], 10000)
	tcp_client.connect()
	tcp_client.send_hello_message()


if __name__ == '__main__':
	sys.exit(main())
