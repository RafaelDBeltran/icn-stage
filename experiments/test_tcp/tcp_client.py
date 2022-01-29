#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

import socket
import sys
import logging
import argparse

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
#DEFAULT_HOST = socket.gethostname()
DEFAULT_HOST = '192.168.133.1'
DEFAULT_PORT = 10000


class TCPClient:

	def __init__(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def connect(self, host_=DEFAULT_HOST, port_=DEFAULT_PORT):
		logging.info('Starting the connection to the server %s %d ' % (host_, port_))
		try:
			self.socket.connect((host_, port_))

		except Exception as e:
			logging.error(e)

	def send_hello_message(self):
		try:
			message = 'Hello World!'
			logging.info('Sending message: ' + str(message))
			self.socket.sendall(message.encode('UTF-8'))

		except Exception as e:
			logging.error(e)

		finally:
			logging.info('Closing Socket')
			self.socket.close()


def main():
	# arguments
	parser = argparse.ArgumentParser(description='A simple TCP client for testing ICN-Stage Controller')

	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)
	parser.add_argument('--host', "-o", help="Server host", default=DEFAULT_HOST)
	parser.add_argument('--port', "-p", help="Server port", default=DEFAULT_PORT, type=int)

	# parser.print_help()

	# read arguments from the command line
	args = parser.parse_args()

	# setup the logging facility

	if args.log == logging.DEBUG:
		logging.basicConfig(filename = "/tmp/actor_logfile.log",
                    		filemode = "w",format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
							datefmt=TIME_FORMAT, level=args.log)

	else:
		logging.basicConfig(filename = "/tmp/actor_logfile.log",
                    		filemode = "w",
							format='%(asctime)s %(message)s',
							datefmt=TIME_FORMAT, level=args.log)

	# shows input parameters
	logging.info("")
	logging.info("INPUT")
	logging.info("---------------------")
	logging.info("\t Logging level : %s" % args.log)
	logging.info("\t Server host   : %s" % args.host)
	logging.info("\t Server port   : %s" % args.port)
	logging.info("")

	logging.info("")
	logging.info("RUN")
	logging.info("---------------------")
	tcp_client = TCPClient()
	tcp_client.connect(args.host, args.port)
	tcp_client.send_hello_message()


if __name__ == '__main__':
	sys.exit(main())
