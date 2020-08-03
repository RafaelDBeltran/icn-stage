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
	parser.add_argument('--udp', "-u", help="use UDP rather than TCP", default=DEFAULT_UDP, action='store_true')

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
	print("")
	print("INPUT")
	print("---------------------")
	print("\t Logging level  : %s" % args.log)
	print("\t Server host    : %s" % args.host)
	print("\t Server port    : %s" % args.port)
	print("\t Time (secs)    : %s" % args.time)
	print("\t UDP            : {}".format(args.udp))
	print("")

	# run iperf3
	client = iperf3.Client()
	print("client ok.")
	client.duration = args.time
	client.server_hostname = args.host
	client.port = args.port
	if args.udp:
		client.protocol = 'udp'

	print("RUN")
	print("---------------------")
	print('\tConnecting to {0}:{1}'.format(client.server_hostname, client.port))
	result = client.run()

	if result.error:
		print(result.error)
	else:
		print('')
		print('\tTest completed:')
		print('\t\tstarted at         {0}'.format(result.time))
		print('\t\tbytes transmitted  {0}'.format(result.bytes))
		print('\t\tjitter (ms)        {0}'.format(result.jitter_ms))
		print('\t\tavg cpu load       {0}%\n'.format(result.local_cpu_total))
		print('')
		print('\tAverage transmitted data:')
		print('\t\tbits per second      (bps)   {0}'.format(result.bps))
		print('\t\tKilobits per second  (kbps)  {0}'.format(result.kbps))
		print('\t\tMegabits per second  (Mbps)  {0}'.format(result.Mbps))
		print('\t\tKiloBytes per second (kB/s)  {0}'.format(result.kB_s))
		print('\t\tMegaBytes per second (MB/s)  {0}'.format(result.MB_s))
	print("done.")


if __name__ == '__main__':
	sys.exit(main())
