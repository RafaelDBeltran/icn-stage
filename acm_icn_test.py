#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-
import sys
import argparse
import os
import logging
import time
import progressbar

# project bibs
from modules.conlib.controller_client import ControllerClient
from modules.conlib.remote_access import Channel
from modules.conlib.controller_client import *
from modules.model.experiment import Experiment
from modules.model.role import Role
from modules.model.worker import Worker
# load tools
from modules.util.tools import ConfigHelper
from modules.util.tools import View
from modules.util.tools import Sundry
# root imports
from zookeeper_controller import Zookeeper_Controller
from experiments_resources import call_tcpserver

# Variables Define
_local_experiments_dir = "./"

# general constants
LOG_LEVEL = logging.DEBUG
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
SECS_TO_ADD_ACTORS = 120

# default value constants
DEFAULT_OUT_FILE = "log.txt"
DEFAULT_USER_NAME = "vagrant"
DEFAULT_PASSWORD = ""
DEFAULT_REMOTE_PKEY_PATH = "/home/vagrant/icn-stage/.vagrant/machines/default/virtualbox/private_key"
DEFAULT_NUMBER_ACTORS = 2


if LOG_LEVEL == logging.DEBUG:
	logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
						datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')
else:
	logging.basicConfig(format='%(asctime)s %(message)s',
						datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')


def add_workers(zookeeper_controller, n_actors):
	logging.info("Adding %d actors..." % n_actors)
	public_key = Sundry.get_pkey(DEFAULT_REMOTE_PKEY_PATH)

	#for h in  range(n_hosts):
	for a in progressbar.progressbar(range(n_actors), redirect_stdout=True):
		logging.info("\tAdding actor %d " % a)
		ip_address = "10.0.0.%d" % (a + 1)
		new_worker = Worker(ip_address, DEFAULT_USER_NAME, DEFAULT_PASSWORD, pkey=public_key)
		zookeeper_controller.controller_client.task_add(COMMANDS.NEW_WORKER, worker=new_worker)
		logging.info("\tWorker {} added.".format(ip_address))

	logging.info("Waiting %s seconds..."%SECS_TO_ADD_ACTORS)
	for i in progressbar.progressbar(range(SECS_TO_ADD_ACTORS), redirect_stdout=True):
		time.sleep(1)

	logging.info("Adding actors... DONE!")


def run_experiments(n_actors=DEFAULT_NUMBER_ACTORS):
	results = {}
	n_experiments = 2

	zc = Zookeeper_Controller()
	zc.zookeeper_start()
	add_workers(zc, n_actors)
	zc.zookeeper_stop()


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
