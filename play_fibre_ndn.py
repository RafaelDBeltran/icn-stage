#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

# general imports
import argparse
import logging
import os
import sys
import subprocess
import threading
from time import sleep
#import commands
import time
import subprocess
from functools import partial
import shlex
import zookeeper_controller as zc

# constants
ICN_STAGE_CMD = ['python3', 'icn-stage.py']
DEFAULT_RUN_DIRECTOR = True
DEFAULT_RUN_MININET = True
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_LOG_LEVEL = logging.INFO

# SLEEP_SECS_TO_FAIL = 60 * 2
# IPERF_INTERVAL_SECS = 1
# EXPERIMENT_LENGTH_SECS = 60 * 10

SLEEP_SECS_TO_FAIL = 100 * 1

EXPERIMENT_LENGTH_SECS = 60 * 10
DIRECTOR_SLEEP_SECS = "1"

FAIL_ACTORS_MODELS = []
FAIL_ACTORS_MODELS += [[False, 2]] # without fail, with recover (avaliable)
FAIL_ACTORS_MODELS += [[True, 1]] # with fail, without recover
FAIL_ACTORS_MODELS += [[True, 2]] # with fail, with recover


MANAGE_DIRECTOR = True
results = []


def get_file_name(fail, actors, experiment_length_secs=EXPERIMENT_LENGTH_SECS):
	fail_str = "OFF"
	if fail:
		fail_str = "ON"

	recover_str = "OFF"
	if actors>1:
		recover_str = "ON"

	name = 'ndn-traffic_results_fail-{}_recover-{}_length-{}s.txt'.format(fail_str, recover_str, experiment_length_secs)
	logging.info(" name: {}".format(name))
	return name


def define_iptables(jump):

	cmd = "cat busyactor.txt"
	#busy_actor = commands.getoutput(cmd)
	busy_actor = subprocess.check_output(cmd, shell = True)
	busy_actor = busy_actor.decode('utf-8')
	logging.info("[CP10.22] commands.getoutput: {}".format(busy_actor))
	

	cmd = "sudo iptables -A INPUT -s {} -j {}".format(busy_actor, jump)
	logging.debug("CMD: {}".format(cmd))
	subprocess.call(cmd, shell = True)
	subprocess.call("sudo iptables save", shell = True)


def introduce_fault():
	busy_actor = None  # "10.0.0.1"
	start_time = time.time()
	
	cmd = "python3 zookeeper_controller.py"

	zc.get_source('10.200.0.6:2181')
	
	# logging.info("[CP10.21] commands.getoutput: {}".format(cmd))
	# output = commands.getoutput(cmd)

	# cmd = "cat busyactor.txt"
	# logging.info("[CP10.22] commands.getoutput: {}".format(cmd))
	# busy_actor = commands.getoutput(cmd)
	# #busy_actor = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=SLEEP_SECS_TO_FAIL)
	# logging.info("[CP10.3] busy_actor: '{}'".format(busy_actor))


	diff_time = time.time() - start_time
	logging.info("\n\n+--- FAIL EVALUATION [CP10.4] diff_time: {}\n".format(diff_time))
	if busy_actor is not None:
		sleep_secs = SLEEP_SECS_TO_FAIL - int(diff_time)
		logging.info("\n\n+--- Sleeping {} secs ...  [CP10.5]".format(sleep_secs))
		sleep(sleep_secs)
		
		#TODO 14/08 bloquear port ndn 6363 e zookeeper #fazer metodo
		define_iptables('DROP')

		logging.info("+--- introducing fail  [CP10.6]---+ busy actor: {} \n".format(busy_actor))

		logging.info("+--- Finish fail ...  [CP10.7]---+\n")
	else:
		raise Exception(" Source not found! ")


def run_play(fail_actors):
	fail = fail_actors[0]
	actors = fail_actors[1]

	logging.info("+--- Begin Evaluation [CP09] ---+\n")
	# # clean zookeeper tree
	cmd = ICN_STAGE_CMD + ['reset']
	logging.info("+--- Clean zookeepeer tree [CP09.1] call: {}\n".format(" ".join(cmd)))
	subprocess.call(cmd)
	logging.info("+--- Clean zookeepeer done [CP09.1.done]\n\n")

	# start actors
	#TODO adicionar 2 parametros, arquivo de json e numero de atores
	cmd = ICN_STAGE_CMD + ['addactors', str(actors)]
	logging.info("+--- Adding actors [CP09.2] call: {}".format(" ".join(cmd)))
	subprocess.call(cmd)
	logging.info("+--- Adding actors done [CP09.2.done]\n\n")


	fault_thread = None
	try:
		if fail:
			logging.info("+--- FAIL EVALUATION [CP10.1fail] ---+\n")
			# run TCP iperf
			# fail_thread = threading.Thread(target=introduce_fault, args=(None, None))

			fault_thread = threading.Thread(target=introduce_fault)

			fault_thread.start()
		else:
			logging.info("+--- NO FAIL EVALUATION [CP10.2nofail] ---+\n")

		cmd = ICN_STAGE_CMD + ['traffic']
		logging.info("[CP10.7] call: {}".format(" ".join(cmd)))
		subprocess.call(cmd)
		#popen = subprocess.Popen(cmd)

		logging.info("")
		logging.info("")

	except Exception as e:
		print("Exception: {} \n\n\n".format(e))

	finally:

		if fault_thread is not None:
			logging.info("waiting for join fail thread... [CP10.5] timeout=---+\n")
			fault_thread.join()
		#TODO restaurar portas
		define_iptables('ACCEPT')

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
		#commands.getoutput(cmd)
		subprocess.call(cmd,shell=True)
		logging.info("\t+--- Stopping director(s)... done. [CP-2.done] ")


def start_director():
	# start director
	logging.info("\t+--- Starting director... [CP-1]")
	cmd = ICN_STAGE_CMD + ['start', "--sleep", DIRECTOR_SLEEP_SECS]
	logging.debug("subprocess.call: {}".format(cmd))
	subprocess.call(cmd)
	logging.debug("\t+--- Starting director done. [CP-1.done] \n\n")


def stop_script(script):
	cmd = "pgrep -f '{}' ".format(script)
	#results = commands.getoutput(cmd)
	results = subprocess.check_output(cmd,shell=True)
	results = results.decode('utf-8')
	for pid in results.split("\n"):
		cmd = "sudo kill {} -SIGKILL".format(pid)
		logging.info("\t+--- Stopping script cmd: {}".format(cmd))
		subprocess.call(cmd,shell=True)
		#commands.getoutput(cmd)


def stop_workers():
	stop_script("daemon_worker.py")


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
	parser = argparse.ArgumentParser(description='*** An NDN-traffic-generator based ICN-Stage Play ***')

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
	logging.info("SETTINGS")
	logging.info("---------------------")
	logging.info("\t Logging level : {}".format(args.log))
	logging.info("\t Fail Actors   : {}".format(FAIL_ACTORS_MODELS))
	logging.info("\n")

	delete_actors_storage()

	results = []
	count_fail = 1
	for fail_actors in FAIL_ACTORS_MODELS:

		if MANAGE_DIRECTOR:
			stop_director()

		if MANAGE_DIRECTOR:
			start_director()

		logging.info("\n\n\n\n")
		logging.info(" ({}/{}) FAIL? ACTORS?: {}".format(count_fail, len(FAIL_ACTORS_MODELS), fail_actors))
		logging.info("---------------------\n")

		stop_workers()
		#subprocess.call("mv ndn_requests_output.txt {}".format(get_file_name(fail_actors[0], fail_actors[1])),shell=True)
		results += [get_file_name(fail_actors[0], fail_actors[1])]
		
		run_play(fail_actors)
		subprocess.call("mv ndn_requests_output.txt {}".format(get_file_name(fail_actors[0], fail_actors[1])),shell=True)
		logging.info("---------------------\n")
		logging.info(" ({}/{}) DONE FAIL? ACTORS?: {}\n\n\n".format(count_fail, len(FAIL_ACTORS_MODELS), fail_actors))
		count_fail += 1


	if MANAGE_DIRECTOR:
		stop_director()

	stop_workers()

	logging.info("")
	logging.info("PLOTTING")
	logging.info("---------------------")
	fileout = "NDN-traffic_length-{}s_dirsleep-{}".format(EXPERIMENT_LENGTH_SECS, DIRECTOR_SLEEP_SECS)
	cmd = "python3 plot.py --type ndn --xlim {} --out {} ".format(EXPERIMENT_LENGTH_SECS, fileout)
	#python3 plot.py --type ndn ndn_requests_output.txt -l 10 -x 600
	for result in results:
		cmd += " " + result

	logging.info("cmd         : {}".format(cmd))
	cmd_shlex = shlex.split(cmd)
	logging.debug("cmd_shlex   : {}".format(cmd_shlex))
	subprocess.call(cmd_shlex)
	logging.info("cmd         : {}".format(cmd))

# subprocess.call(cmd)
if __name__ == '__main__':
		sys.exit(main())
