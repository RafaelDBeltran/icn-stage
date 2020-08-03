#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

import socket
import sys
import logging
import argparse
import iperf3

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
#DEFAULT_HOST = socket.gethostname()
DEFAULT_HOST = '192.168.133.1'
DEFAULT_PORT = 10000
DEFAULT_TIME = 10
DEFAULT_UDP = False


def main():
	# arguments
	parser = argparse.ArgumentParser(description='A Iperf3 client wrapper for performance evaluation within ICN-Stage')

	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)
	parser.add_argument('--host', "-o", help="server host", default=DEFAULT_HOST)
	parser.add_argument('--port', "-p", help="server port", default=DEFAULT_PORT, type=int)
	parser.add_argument('--time', "-t", help="time in seconds to transmit", default=DEFAULT_TIME, type=int)
	parser.add_argument('--udp', "-u", help="use UDP rather than TCP", default=DEFAULT_UDP, type=bool)

	# read arguments from the command line
	args = parser.parse_args()

	# setup the logging facility
	if args.log == logging.DEBUG:
		logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
							datefmt=TIME_FORMAT, level=args.log, filemode='w', filename='tcp_client.log')

	else:
		logging.basicConfig(format='%(asctime)s %(message)s',
							datefmt=TIME_FORMAT, level=args.log, filemode='w', filename='tcp_client.log')

	# shows input parameters
	logging.info("")
	logging.info("INPUT")
	logging.info("---------------------")
	logging.info("\t Logging level  : %s" % args.log)
	logging.info("\t Server host    : %s" % args.host)
	logging.info("\t Server port    : %s" % args.port)
	logging.info("\t Time (secs)    : %s" % args.time)
	logging.info("\t UDP            : {}".format(args.udp))
	logging.info("")

	client = iperf3.Client()
	client.duration = args.time
	client.server_hostname = args.host
	client.port = args.port
	client.run()


if __name__ == '__main__':
	sys.exit(main())
