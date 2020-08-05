#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import argparse
import logging
import os
import sys
import subprocess
import threading
from time import sleep
import commands

from mininet.log import setLogLevel, info
from mininet.net import Mininet
from mininet.cli import CLI

from functools import partial
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
#from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from mininet.nodelib import NAT

ICN_STAGE_CMD = ['python3', 'icn-stage.py']
DEFAULT_RUN_DIRECTOR = True
DEFAULT_RUN_MININET = True
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_LOG_LEVEL = logging.INFO


def fail_link(net, source, dest, sleep_secs=30):
	sleep(sleep_secs)
	net.delLinkBetween(source, dest)

def run_play(fail=False, director=False, mininet=False):


	#setLogLevel('info')

	# parser = argparse.ArgumentParser()
	# parser.add_argument('--face-type', dest='faceType', default='udp', choices=['udp', 'tcp'])
	# parser.add_argument('--routing', dest='routingType', default='link-state',
	#                      choices=['link-state', 'hr', 'dry'],
	#                      help='''Choose routing type, dry = link-state is used
	#                              but hr is calculated for comparision.''')

	logging.info("\n**** Begin Cleaning ****\n")

	# delete actors past
	for a in range(3):
		# cmd = "for d in 1 2 3 4 5 6 7; do rm -rf actor_$d; done"
		cmd = "rm -rf ~/actor_mininet_{}".format(a)
		print(cmd)
		subprocess.call(cmd, shell=True)

	# cmd = "rm -f iperf*"
	# print(cmd)
	# subprocess.call(cmd, shell=True)

	logging.info("\n**** End Cleaning ****\n")

	if not mininet:
		logging.info("\n**** Skipping Mininet ****\n")
	else:
		logging.info("\n**** Begin Mininet ****\n")
		# cleanning minnet, for the sake of safety
		cmd = ["sudo", "mn", "--clean"]
		subprocess.call(cmd)

		net = Mininet(switch=OVSKernelSwitch,
					  controller=OVSController, waitConnected=True)

		info('*** Adding controller\n')
		net.addController('c0')

		info('*** Adding NAT\n')
		nat = net.addHost('nat', cls=NAT, ip='10.0.0.99', inNamespace=False)

		h1 = net.addHost('h1', ip='10.0.0.1', inNamespace=True)
		h2 = net.addHost('h2', ip='10.0.0.2', inNamespace=True)
		#h3 = net.addHost('h3', ip='10.0.0.3', inNamespace=True)

		s1 = net.addSwitch('s1')

		# Add links
		# bw in Mbit/s
		host_link = partial(TCLink, bw=1)
		net.addLink(h1, s1, cls=host_link)
		net.addLink(h2, s1, cls=host_link)
		# net.addLink(h3, s1, cls=host_link)
		net.addLink(nat, s1)

		net.start()

		info("\n*** starting SSH daemons\n")
		ssh_cmd = '/usr/sbin/sshd'
		opts = '-D'
		for host in net.hosts:
			host.cmd(ssh_cmd + ' ' + opts + '&')

		logging.info("\n**** End Mininet ****\n")

	if not director:
		logging.info(" Skipping director!")

	else:
		# start director
		logging.info("Starting director...")
		subprocess.call(ICN_STAGE_CMD + ['start'])

	logging.info("\n**** Begin Evaluation ****\n")
	# clean zookeeper tree
	subprocess.call(ICN_STAGE_CMD + ['reset'])

	# start actors
	subprocess.call(ICN_STAGE_CMD + ['addactors'])

	try:

		if fail:
			busy_actor = ""
			while busy_actor == "":
				sleep(5)
				cmd = ["python3", "zookeeper_controller.py"]
				logging.info("cmd: {}".format(cmd))
				#busy_actor = subprocess.getoutput(cmd)
				busy_actor = commands.getoutput(cmd)
				logging.info("busy_actor: {}".format(busy_actor))

			# if busy_actor is None:
			# 	raise("Source not found.")
			#
			# else:
			source = None
			for host in net.hosts:
				print("host: {} IP: {}".format(host, host.IP))
				if busy_actor in host.IP:
					source = host
					print("host found! source: {} ".format(host))
			sleep_secs = 60 * 2
			fail_thread = threading.Thread(target=fail_link(net, source, s1, sleep_secs))
			fail_thread.start()

			# run TCP iperf
			subprocess.Popen(ICN_STAGE_CMD + ['iperf', 'iperf_with_fail.log'])

		else:
			subprocess.call(ICN_STAGE_CMD + ['iperf', 'iperf_without_fail.log'])

	except Exception as e:
		print("Exception: {} ".format(e))

	finally:

		logging.info("\n**** End Evaluation ****\n")

		logging.info("\n**** Begin Finishing ****\n")

		if director:
			# start director
			logging.info("Stopping director...")
			subprocess.call(ICN_STAGE_CMD + ['stop'])

		else:
			logging.debug("No director! No needed to stop it.")

		# info("\n*** Type 'exit' or control-D to shut down network\n")
		# CLI(net)
		sleep(5)
		cmd = "sudo pkill iperf3"
		subprocess.call(cmd, shell=True)

		if mininet:
			info("\n*** stopping SSH daemons\n")
			for host in net.hosts:
				host.cmd('kill %' + ssh_cmd)

			info("\n*** mininet network\n")
			net.stop()

		logging.info("\n**** End Finishing ****\n")


def main():
	# arguments
	parser = argparse.ArgumentParser(description='*** An Iperf3 ICN-Stage Play ***')

	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--log", "-l", help=help_msg, default=logging.DEBUG, type=int)
	parser.add_argument('--director', "-d", help="run director ", default=DEFAULT_RUN_DIRECTOR, action='store_true')
	parser.add_argument('--mininet', "-m", help="run mininet ", default=DEFAULT_RUN_MININET, action='store_true')

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
	logging.info("\t Logging level : %s" % args.log)
	logging.info("\t Run mininet?  : {}".format(args.mininet))
	logging.info("\t Run director? : {}".format(args.director))
	#logging.info("\t Run director? : {}".format(args.director))
	logging.info("")
	#run_play(args.director, args.mininet)

	for fail in [True]:
		run_play(fail, args.director, args.mininet)

if __name__ == '__main__':
	#cmd = ["python3", "zookeeper_controller.py"]
	#cmd = "python3 zookeeper_controller.py"
	#logging.info("cmd: {}".format(cmd))
	#busy_actor = commands.getoutput(cmd)

	sys.exit(main())




	#sys.exit(main())
