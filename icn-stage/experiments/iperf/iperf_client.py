#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

import socket
import subprocess
import sys
import logging
import argparse

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_LOGGING_LEVEL = logging.INFO
#DEFAULT_HOST = socket.gethostname()
DEFAULT_HOST = '192.168.133.1'
DEFAULT_PORT = 10000
DEFAULT_TIME = 10
DEFAULT_UDP = False


def main():
	# arguments
	parser = argparse.ArgumentParser(description='A Iperf3 client wrapper for performance evaluation within ICN-Stage')

	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--log", "-l", help=help_msg, default=DEFAULT_LOGGING_LEVEL, type=int)
	parser.add_argument('--host', "-o", help="server host", default=DEFAULT_HOST)
	parser.add_argument('--port', "-p", help="server port", default=DEFAULT_PORT, type=int)
	parser.add_argument('--time', "-t", help="time in seconds to transmit", default=DEFAULT_TIME, type=int)
	parser.add_argument('--udp', "-u", help="use UDP rather than TCP", default=DEFAULT_UDP, action='store_true')

	# read arguments from the command line
	args = parser.parse_args()

	# setup the logging facility
	if args.log == logging.DEBUG:
		logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
							datefmt=TIME_FORMAT, level=args.log)

	else:
		logging.basicConfig(format='%(asctime)s %(message)s',
							datefmt=TIME_FORMAT, level=args.log)

	# shows input parameters
	logging.info("")
	logging.info("INPUT")
	logging.info("---------------------")
	logging.info("\t Logging level  : {}".format(args.log))
	logging.info("\t Server host    : {}".format(args.host))
	logging.info("\t Server port    : {}".format(args.port))
	logging.info("\t Time (secs)    : {}".format(args.time))
	logging.info("\t UDP            : {}".format(args.udp))
	logging.info("")

	logging.info("RUN")
	logging.info("---------------------")

	udp = ""
	if args.udp:
		udp = "--udp"

	# # run iperf2
	cmd = "iperf --client {} --window 1024 --port {} --time {} {}".format(args.host, args.port, args.time, udp)
	print(cmd)
	result = subprocess.call(cmd, shell=True)
	print(result)


if __name__ == '__main__':
	sys.exit(main())
