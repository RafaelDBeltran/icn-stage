#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-
import sys
import argparse
import os, sys, time, logging, time

from mininet.net import Mininet
from mininet.node import UserSwitch, OVSKernelSwitch, Controller
from mininet.topo import Topo
from mininet.log import lg, info
from mininet.util import irange, quietRun
from mininet.link import TCLink
from functools import partial

from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call


LOG_LEVEL = logging.DEBUG
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_OUT_FILE = "log.txt"

if LOG_LEVEL == logging.DEBUG:
	logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
						datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')
else:
	logging.basicConfig(format='%(asctime)s %(message)s',
						datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')


class Dumbbell(Topo):
	"""Dumbbell topology example.
	Two directly connected switches plus a host for each switch:

	   host --- switch --- switch --- host
	   host --- /               \ --- host
	Adding the 'topos' dict with a key/value pair to generate our newly defined
	topology enables one to pass in '--topo=mytopo' from the command line.
	"""

	def __init__(self):
		"Create custom topo."

		# Initialize topology
		Topo.__init__(self)

		# Add hosts and switches
		leftHost1 = self.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)
		leftHost2 = self.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)
		rightHost1 = self.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
		rightHost2 = self.addHost('h4', cls=Host, ip='10.0.0.4', defaultRoute=None)

		leftSwitch = self.addSwitch('s1')
		rightSwitch = self.addSwitch('s2')

		# Add links
		self.addLink(leftHost1, leftSwitch)
		self.addLink(leftHost2, leftSwitch)

		self.addLink(rightSwitch, rightHost1)
		self.addLink(rightSwitch, rightHost2)

		self.addLink(leftSwitch, rightSwitch)


def run_experiments():
	results = {}
	n_hosts = 4
	n_experiments = 2
	topo = Dumbbell()

	info("*** testing datapath\n")
	link = partial(TCLink, delay='2ms', bw=10)
	net = Mininet(topo=topo, switch=OVSKernelSwitch,
				  controller=Controller, waitConnected=True,
				  link=link)
	net.start()
	info("*** testing basic connectivity\n")
	for i in range(n_hosts):
		net.ping([net.hosts[0], net.hosts[n_hosts]])

	for e in range(n_experiments):
		info("*** experiment %d \n"%e)
		results[e] = []
		info("*** testing bandwidth\n")
		for h in range(n_hosts):
			src, dst = net.hosts[0], net.hosts[h]
			# Try to prime the pump to reduce PACKET_INs during test
			# since the reference controller is reactive
			src.cmd('telnet', dst.IP(), '5001')
			info("testing", src.name, "<->", dst.name, '\n')
			# serverbw = received; _clientbw = buffered
			serverbw, _clientbw = net.iperf([src, dst], seconds=10)
			info(serverbw, '\n')
			sys.stdout.flush
			results[e] += [(h, serverbw)]
	net.stop()

	for e in range(n_experiments):
		info("\n*** Linear network results for experiment ", e ,":\n")
		result = results[e]
		info("SwitchCount\tiperf Results\n")
		for switchCount, serverbw in result:
			info(switchCount, '\t\t')
			info(serverbw, '\n')
		info('\n')
	info('\n')

def main():
	# arguments
	parser = argparse.ArgumentParser(description='ICN-Stage Demo Experiment')

	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--out", "-o", help=help_msg, default=DEFAULT_OUT_FILE)

	# cmd_choices = ['start', 'stop', 'restart', 'status']
	# parser.add_argument('cmd', choices=cmd_choices)

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
	logging.info("\t logging level : %s" % args.log)
	logging.info("\t out file      : %s" % args.out)
	logging.info("")

	run_experiments()


if __name__ == '__main__':
	sys.exit(main())