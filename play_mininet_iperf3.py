#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

# general imports
import argparse
import logging
import os
import sys
import subprocess
import threading
from time import sleep
import commands
import time
import subprocess
from functools import partial

# mininet imports
from mininet.log import setLogLevel, info
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
#from mininet.cli import CLI
#from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from mininet.nodelib import NAT

# constants
ICN_STAGE_CMD = ['python3', 'icn-stage.py']
DEFAULT_RUN_DIRECTOR = True
DEFAULT_RUN_MININET = True
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_LOG_LEVEL = logging.DEBUG
SLEEP_SECS_TO_FAIL = 60 * 2
IPERF_INTERVAL_SECS = 5
EXPERIMENT_LENGTH_SECS = 60 * 5

FAIL_ACTORS_MODELS = []
FAIL_ACTORS_MODELS += [[True, 2]] # with fail, with recover
#FAIL_ACTORS_MODELS += [[True, 1]] # with fail, without recover
#FAIL_ACTORS_MODELS += [[False, 2]] # without fail, with recover (avaliable)



def get_file_name(fail, actors, iperf_interval_secs=IPERF_INTERVAL_SECS, experiment_length_secs=EXPERIMENT_LENGTH_SECS):
	fail_str = "OFF"
	if fail:
		fail_str = "ON"

	recover_str = "OFF"
	if actors>1:
		recover_str = "ON"

	name = 'results_fail-{}_recover-{}_interval-{}s_length-{}s.json'.format(fail_str, recover_str, iperf_interval_secs, experiment_length_secs)
	logging.info(" name: {}".format(name))
	return name

#FAIL_ON_LOG_FILE_NAME = 'results_fail_ON_{}s.json'.format(IPERF_INTERVAL_SECS)
#FAIL_OFF_LOG_FILE_NAME = 'results_fail_OFF_{}s.json'.format(IPERF_INTERVAL_SECS)
#from subprocess import STDOUT, check_output



def get_host(net, addr):
	result = None
	for host in net.hosts:
		logging.debug("host: {} IP: {}".format(host, host.IP))
		if addr in "{}".format(host.IP):
			result = host
			logging.info("Result host found! source: {} ".format(host))
	return result


def introduce_fail(net, destination):
	busy_actor = None  # "10.0.0.1"
	start_time = time.time()

	cmd = "python3 zookeeper_controller.py"
	logging.info("[CP10.21] commands.getoutput: {}".format(cmd))
	output = commands.getoutput(cmd)

	cmd = "cat busyactor.txt"
	logging.info("[CP10.22] commands.getoutput: {}".format(cmd))
	busy_actor = commands.getoutput(cmd)
	#busy_actor = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=SLEEP_SECS_TO_FAIL)
	logging.info("[CP10.3] busy_actor: '{}'".format(busy_actor))

	diff_time = time.time() - start_time
	logging.info("\n\n+--- FAIL EVALUATION [CP10.4] diff_time: {}\n".format(diff_time))

	source = get_host(net, busy_actor)
	if source is not None:
		sleep_secs = SLEEP_SECS_TO_FAIL - int(diff_time)
		logging.info("\n\n+--- Sleeping {}secs ...  [CP10.5]".format(sleep_secs))
		sleep(sleep_secs)
		#net.configLinkStatus(source, destination, 'down')
		net.delLinkBetween(source, destination)
		logging.info("\n\n+--- Finish fail ...  [CP10.6]---+\n")
	else:
		raise Exception(" Source not found! ")


def start_mininet():
	logging.info("+--- Begin Mininet [CP02] ---+\n")
	# cleanning minnet, for the sake of safety
	cmd = ["sudo", "mn", "--clean"]
	logging.debug("\t\t subprocess.call cmd: {}".format(cmd))
	subprocess.call(cmd)
	logging.info("")
	logging.info("")
	net = Mininet(switch=OVSKernelSwitch,
				  controller=OVSController, waitConnected=True)

	logging.info('*** Adding controller [CP03] \n')
	net.addController('c0')
	logging.info("")
	logging.info('*** Begin adding NAT & hosts [CP04]\n')
	nat = net.addHost('nat', cls=NAT, ip='10.0.0.99', inNamespace=False)
	h1 = net.addHost('h1', ip='10.0.0.1', inNamespace=True)
	h2 = net.addHost('h2', ip='10.0.0.2', inNamespace=True)
	# h3 = net.addHost('h3', ip='10.0.0.3', inNamespace=True)
	logging.info('*** End Adding NAT & hosts [CP04.done]\n')

	logging.info('*** Adding switch and links [CP05]\n')
	s1 = net.addSwitch('s1')

	logging.info('*** Begin adding links [CP06]\n')
	# Add links
	# bw in Mbit/s
	host_link = partial(TCLink, bw=1)
	net.addLink(h1, s1, cls=host_link)
	net.addLink(h2, s1, cls=host_link)
	# net.addLink(h3, s1, cls=host_link)
	net.addLink(nat, s1)
	logging.info('*** End adding switch and links [CP06.done]\n\n')

	logging.info('Starting network [CP07]\n')
	net.start()
	logging.info("")
	logging.info("")

	logging.info("+--- starting SSH daemons [CP08] ---+\n")
	ssh_cmd = '/usr/sbin/sshd -D &'
	for host in net.hosts:
		logging.info("host: {} ssh_cmd: {}".format(host, ssh_cmd))
		host.cmd(ssh_cmd)
	logging.info("+--- starting SSH daemons done [CP08.done]\n\n")

	return net, h1, h2, s1


def run_play(net, h1, h2, s1, fail_actors):
	fail = fail_actors[0]
	actors = fail_actors[1]

	logging.info("+--- Begin Evaluation [CP09] ---+\n")
	# # clean zookeeper tree
	cmd = ICN_STAGE_CMD + ['reset']
	logging.info("+--- Clean zookeepeer tree [CP09.1] call: {}\n".format(" ".join(cmd)))
	subprocess.call(cmd)
	logging.info("+--- Clean zookeepeer done [CP09.1.done]\n\n")

	# start actors
	cmd = ICN_STAGE_CMD + ['addactors']
	logging.info("+--- Adding actors [CP09.2] call: {}".format(" ".join(cmd)))
	subprocess.call(cmd)
	logging.info("+--- Adding actors done [CP09.2.done]\n\n")

	if actors == 1:
		#net.addLink(h2, s1, cls=host_link)
		logging.info("+--- Removing the link from h2 to s1 [CP09.3]")
		#net.configLinkStatus(h2, s1, 'down')
		net.delLinkBetween(h2, s1)

	else:
		net.addLink(h2, s1)
		#net.configLinkStatus(h2, s1, 'up')

	fail_thread = None
	try:
		if fail:
			logging.info("+--- FAIL EVALUATION [CP10.1fail] ---+\n")
			# run TCP iperf
			# fail_thread = threading.Thread(target=introduce_fail, args=(None, None))
			fail_thread = threading.Thread(target=introduce_fail, args=(net, s1,))
			fail_thread.start()
		else:
			logging.info("+--- NO FAIL EVALUATION [CP10.2nofail] ---+\n")

		cmd = ICN_STAGE_CMD + ['iperf', get_file_name(fail, actors), str(IPERF_INTERVAL_SECS), str(EXPERIMENT_LENGTH_SECS)]
		logging.info("[CP10.7] call: {}".format(" ".join(cmd)))
		subprocess.call(cmd)
		#popen = subprocess.Popen(cmd)

		# else:
		# 	cmd = ICN_STAGE_CMD + ['iperf', get_file_name(fail, actors), str(IPERF_INTERVAL_SECS)]
		# 	logging.info("+--- NO FAIL EVALUATION [CP10.1nofail] cmd: {}".format(" ".join(cmd)))
		# 	subprocess.call(cmd)

		logging.info("")
		logging.info("")

	except Exception as e:
		print("Exception: {} \n\n\n".format(e))

	finally:
		if fail_thread is not None:
			logging.info("waiting for join fail thread... [CP10.5] timeout=---+\n")
			fail_thread.join()
		logging.info("")
		logging.info("")


def stop_director():
		# stop director
		cmd = ICN_STAGE_CMD + ['stop']
		logging.info("Stopping director... [CP11] {}\n".format(" ".join(cmd)))
		subprocess.call(cmd)
		logging.info("")
		logging.info("")
		# stop director
		stop_script("daemon_director.py")

		cmd = "rm -f /tmp/daemon_director_default.pid"
		logging.info("\t+--- Removing director pid cmd: {}".format(cmd))
		commands.getoutput(cmd)
		logging.info("\t+--- Stopping director(s)... done. [CP-2.done] ")


def start_director():
	# start director
	logging.info("\t+--- Starting director... [CP-1]")
	cmd = ICN_STAGE_CMD + ['start']
	logging.debug("subprocess.call: {}".format(cmd))
	subprocess.call(cmd)
	logging.debug("\t+--- Starting director done. [CP-1.done] \n\n")


def stop_script(script):
	cmd = "pgrep -f {}".format(script)
	results = commands.getoutput(cmd)
	for pid in results.split("\n"):
		cmd = "sudo kill {}".format(pid)
		logging.info("\t+--- Stopping script cmd: {}".format(cmd))
		commands.getoutput(cmd)


def stop_workers():
	stop_script("daemon_worker.py")


def stop_iperf3():
		cmd = "sudo pkill iperf3"
		logging.info("Stopping iperf3... [CP12] cmd: {}\n".format(cmd))
		subprocess.call(cmd, shell=True)
		stop_script("iperf3_client.py")
		logging.info("")
		logging.info("")


def stop_mininet(net):
		logging.info("+--- begin stopping SSH daemons [CP13] ---+\n")
		for host in net.hosts:
			cmd = 'kill /usr/sbin/sshd'
			logging.info("\t\t host: {} cmd: {}".format(host, cmd))
			host.cmd(cmd)
		logging.info("+--- end stopping SSH daemons [CP13.done] ---+\n")

		logging.info("+--- Stopping mininet network [CP14]---+\n")
		net.stop()


def delete_actors_storage():
	# delete actors
	logging.info("+--- Deleting actors storage [CP-3] ---+")
	for a in range(3):
		cmd = "rm -rf ~/actor_mininet_{}".format((a+1))
		logging.info("\t\t cmd: {}".format(cmd))
		subprocess.call(cmd, shell=True)
	cmd = "rm -f /tmp/daemon_worker_*"
	logging.info("\t\t cmd: {}".format(cmd))
	logging.debug("+--- End Deleting actors storage [CP-3.done] ---+\n")


def main():

	# parse arguments
	parser = argparse.ArgumentParser(description='*** An Iperf3 based ICN-Stage Play ***')

	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--log", "-l", help=help_msg, default=DEFAULT_LOG_LEVEL, type=int)

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
	logging.info("\t Logging level : {}".format(args.log))
	logging.info("\t Fail Actors   : {}".format(FAIL_ACTORS_MODELS))
	logging.info("\n")

	delete_actors_storage()
	stop_director()

	net, h1, h2, s1 = start_mininet()
	start_director()

	count_fail = 1
	for fail_actors in FAIL_ACTORS_MODELS:
		logging.info("\n\n\n\n")
		logging.info(" ({}/{}) FAIL? ACTORS?: {}".format(count_fail, len(FAIL_ACTORS_MODELS), fail_actors))
		logging.info("---------------------\n")
		stop_iperf3()
		stop_workers()
		run_play(net, h1, h2, s1, fail_actors)
		logging.info("---------------------\n")
		logging.info(" ({}/{}) DONE FAIL? ACTORS?: {}\n\n\n".format(count_fail, len(FAIL_ACTORS_MODELS), fail_actors))
		count_fail += 1

	stop_mininet(net)
	stop_director()
	stop_iperf3()

if __name__ == '__main__':
		sys.exit(main())
