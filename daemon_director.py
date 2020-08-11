#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

#
#	@original author: Nelson Antonio Antunes Junior
#	@email: nelson.a.antunes at gmail.com
#	@date: (DD/MM/YYYY) 24/01/2017

import argparse
import socket
import multiprocessing
import subprocess
import datetime
import tarfile
import os
import logging
#sys.path.append(r'~/myRuns/modules')

# icn-stage bibs
from modules.conlib.controller_client import *
from modules.conlib.remote_access import Channel
from modules.model import worker
from zookeeper_controller import ZookeeperController
from modules.extralib.daemon import Daemon
from modules.model.worker import Worker
from modules.model.experiment import Experiment
from modules.model.role import Role

'''
data = json.load(open('config.json'))
my_adapter_ip = ConfigHelper(data["zookeeper_adapter"])
'''
LOG_LEVEL = logging.DEBUG
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_SLEEP_SECONDS = 30

_controllerport = "2181"
_pyvers = "3.6.9"
_timeout = 2
#_worker_daemon = "daemon_worker.py"
_worklibtarfile = "worklib.tar.gz"

# TODO#
# _local_experiments_dir = os.path.expanduser("~/controller/experiments/")
# _local_experiments_dir = os.path.expanduser("/home/rafael/Documents/ExtendEasyExp/")
_local_experiments_dir = os.path.expanduser("./")


def create_worklib(output_file_):
	# setup
	# modules_source_path = "./modules/"
	worklib_source_path = "./modules/worklib/"
	extralib_source_path = "./modules/extralib/"

	# creates tar file
	tar_file = tarfile.open(output_file_, "w:gz")

	# add main file
	tar_file.add(worker.SCRIPT)

	# add modules
	current_dir = os.getcwd()
	# os.chdir(modules_source_path)
	for d in [worklib_source_path, extralib_source_path]:

		for f in os.listdir(d):
			file = "%s/%s" % (d, f)
			logging.debug("File: %s" % file)
			if file.endswith('.py'):
				logging.debug("adding %s" % file)
				tar_file.add("%s" % (file))
			else:
				logging.debug("skiping %s" % file)
			# logging.debug(file)

	# close file
	tar_file.close()
	os.chdir(current_dir)


def get_ip():
	return [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
			[socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]


# _realocate_timeout = 240
# _restart_timeout = _realocate_timeout / 2


# RPM = Resource Pool Manager
class RPM(multiprocessing.Process):
#class RPM(threading.Thread):

	def __init__(self, sleep_seconds, zk_addr):
		super().__init__()
		self.sleep_seconds = DEFAULT_SLEEP_SECONDS
		#self.controller_client = None
		self.zk_addr = zk_addr

	# def set_sleep_seconds(self, sleep_seconds):
	# 	self.sleep_seconds = sleep_seconds

	# def set_controller_client(self, controller_client):
	# 	logging.debug(" Controller_client: {}".format(controller_client))
	# 	self.controller_client = controller_client

	# def set_new_controller_client(self, zookeeper_ip_port):
	# 	self.controller_client = ControllerClient(zookeeper_ip_port)
	# 	logging.debug(" self.Controller_client: {}".format(self.controller_client))

	def run(self):
		logging.info("RPM[CP1]")
		exit = False

		run_controller_client = ControllerClient(self.zk_addr)
		workers = run_controller_client.worker_get_all()

		workers_disconnected = set([])
		if len(workers) > 0:
			workers_disconnected = set([x for x in workers if x.status != 'BUSY' or x.status != 'IDLE'])
		workers = set(workers)

		starting_time = time.time()
		last = starting_time
		while not exit:
			now = time.time()
			logging.debug("RPM[CP1.1] now: ".format(now))

			try:
				with open("rpm_activity.log", "w+") as fa:
					print("%16s, \t%50s, \t%13s, \t%24s, \t%24s" % (
					'ACTIVE_TIME', 'HOSTNAME', 'STATUS', 'LAST_CALL', 'WHEN_DISCONNECT'), file=fa)

					for worker in sorted(run_controller_client.worker_get_all(), key=lambda x: x.hostname):

						logging.debug("RPM[CP2] worker hostname: {} status: {}".format(worker.hostname, worker.status))
						if worker.status == 'BUSY' or worker.status == 'IDLE':
							if worker.hostname in workers_disconnected or not (worker in workers):
								run_controller_client.worker_update_connection_time(worker.path, now)
								workers_disconnected.discard(worker.hostname)

						else:
							workers_disconnected.add(worker.hostname)

							if worker.status == 'NEW LOST BUSY' or worker.status == 'LOST BUSY':
								if not worker.actors:
									break
								with open('failures_recov.txt', 'a+') as fi:
									print(time.time(), worker.hostname, worker.actors, file=fi)

								logging.debug("RPM [CP6] worker.status")
								run_controller_client.worker_add_disconnected(worker.hostname, 'RECOVERING')
								run_controller_client.task_add(COMMANDS.RECOVER_ACTOR, worker=worker)

							elif worker.status == 'LOST IDLE' or worker.status == 'NEW LOST IDLE':
								logging.debug("RPM[CP7] RecoverActor")
								run_controller_client.worker_add_disconnected(worker.hostname, 'RESTARTING')

								logging.debug("RPM[CP8] COMMANDS.START_WORKER")
								run_controller_client.task_add(COMMANDS.START_WORKER, worker=worker)

							else:
								logging.debug("RPM[CP8] OTHER STATUS: '{}'".format(worker.status))

								status = ""
								if worker.status == ' 2 1':
									status = "RECOVERING"
								else:
									status = worker.status

								status_count = 1
								status_split = status.split(' ')
								new_status = "{} {}".format(status, status_count)

								if len(status_split) > 1 and status_split[-1].isnumeric():
									status_count = int(status_split[-1]) + 1
									new_status = "{} {}".format(" ".join(status_split[:-1]), status_count)

								# after N loops try again...
								if status_count > 10:
									logging.debug("RPM [CP6] worker.status")
									run_controller_client.worker_add_disconnected(worker.hostname, 'RECOVERING')
									run_controller_client.task_add(COMMANDS.RECOVER_ACTOR, worker=worker)

								else:
									logging.debug("RPM[CP11] new_status: {}".format(new_status))
									run_controller_client.worker_add_disconnected(worker.hostname, new_status)

						workers.add(worker)

						dcnx_time = ''
						if worker.disconnection_time != 0:
							dcnx_time = time.ctime(worker.disconnection_time)

						last_login = ''
						if worker.connection_time != 0:
							last_login = time.ctime(worker.connection_time)

						print("%16f, \t%50s, \t%13s, \t%24s, \t%24s" % (
							worker.active_time, worker.hostname, worker.status, last_login, dcnx_time), file=fa)

			except Exception as e:
				logging.error("RPM[CP99] Exception: {}".format(e))

				with open("rpm_output.log", "a+") as fo:
					print(time.time(), worker.hostname, " exception: ", e, file=fo)

			finally:
				fa.close()

			last = now
			time.sleep(self.sleep_seconds)

		run_controller_client.close()


class DirectorDaemon(Daemon):

	def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
		super().__init__(pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null')
		self.zookeeper_controller = ZookeeperController()
		self.sleep_seconds = DEFAULT_SLEEP_SECONDS
		self.controller_client = None
		self.zookeeper_ip_port = self.zookeeper_controller.zookeeper_ip_port

	def set_sleep_seconds(self, sleep_seconds):
		self.sleep_seconds = sleep_seconds
		logging.debug("self.sleep_seconds: {}".format(self.sleep_seconds))

	def task_handler(self, tasks_new):

		logging.debug("task_handler tasks_new: %s" % str(tasks_new))
		for task_now in sorted(tasks_new):
			logging.debug("\ttask_now: %s" % str(task_now))
			task_data, task_args = self.controller_client.task_get(task_now)
			logging.debug("\ttask_data: %s" % str(task_data))
			logging.debug("\ttask_args: %s" % str(task_args))

			task_cmd = (task_data[:4]).decode("utf-8")
			# logging.debug("\ttask_NEW_WORKER: %s" % str(COMMANDS.NEW_WORKER))
			logging.debug("\ttask_CMD: %s" % str(task_cmd))

			if task_cmd == COMMANDS.SEND_EXPERIMENT:

				logging.debug("SEND_EXPERIMENT 1")

				exp = Experiment.decode(task_args["experiment"].decode('utf-8'))
				logging.debug("SEND_EXPERIMENT 2")
				no_workers_total = 0
				for role in exp.roles:
					logging.debug('role %s', role)
					logging.debug('role.no_workers %s', role.no_workers)
					no_workers_total += role.no_workers
					logging.debug('no_workers_total %s', no_workers_total)
				logging.debug("SEND_EXPERIMENT 3")
				worker_path_list = []
				worker_path_list = self.controller_client.worker_allocate(no_workers_total, alloc_list=worker_path_list)
				logging.debug("SEND_EXPERIMENT 4")
				logging.debug("worker_path_list %s", worker_path_list)
				ready = []
				failed = False
				logging.debug("SEND_EXPERIMENT 4.5 %s", no_workers_total)
				if worker_path_list:
					last = 0
					logging.debug("SEND_EXPERIMENT 5")
					for role in exp.roles:
						remaining = role.no_workers
						tries = len(worker_path_list)  # number of possible allocate workers
						logging.debug("SEND_EXPERIMENT 6 remaining: {}".format(remaining))
						i = 0
						# worker_path_list = [new_path.decode('utf-8') for new_path in worker_path_list]
						while remaining and tries > 0:
							try:
								logging.debug("SEND_EXPERIMENT 6.5 actor: {}".format(worker_path_list[last + i]))
								worker = self.controller_client.worker_get(worker_path_list[last + i])

								logging.debug("SEND_EXPERIMENT 7")
								logging.info(" connecting to %s " % worker.hostname)
								channel = Channel(hostname=worker.hostname, username=worker.username,
												  password=worker.password, pkey=worker.pkey, timeout=_timeout)

								remote_path = worker.get_remote_experiment_path()
								logging.debug("SEND_EXPERIMENT 7.1 changing dir to {} ".format(remote_path))
								channel.chdir(remote_path)
								if type(exp.name) is bytes:
									exp.name = exp.name.decode('utf-8')

								logging.info("SEND_EXPERIMENT 7.2 making dir {}".format(exp.name))
								channel.mkdir(exp.name)

								logging.info("SEND_EXPERIMENT 7.3 changing to dir {}".format(exp.name))
								channel.chdir(exp.name)

								if exp.filename is not None and exp.filename != "":
									logging.debug("SEND_EXPERIMENT 8 file: {} to: {}".format(
										_local_experiments_dir + exp.filename, remote_path))
									channel.put(_local_experiments_dir + exp.filename, exp.filename)

									logging.debug("SEND_EXPERIMENT 9 unzipping file {}".format(exp.filename))
									channel.run("tar -xzf %s" % exp.filename)
									logging.debug("SEND_EXPERIMENT 10 unzipping done.")

								actor_id = self.controller_client.exp_create_actor(exp.id, worker.path, role.id)
								channel.run(
									"echo \"parameters=%s\nexp_id=%s\nrole_id=%s\nactor_id=%s\nis_snapshot=%s\" > info.cfg" % (
									role.parameters, exp.id, role.id, actor_id, exp.is_snapshot))
								logging.debug("SEND_EXPERIMENT 11")
								channel.close()
								remaining -= 1
								i += 1
								ready.append((worker.path, actor_id))

							except Exception as e:
								tries -= 1
								# print(datetime.datetime.now(), " ##Exception: ", e)
								logging.error('SEND_EXPERIMENT Try: {} Exception: {}'.format(tries, e))
								logging.error("SEND_EXPERIMENT 12")
								new_worker = self.controller_client.worker_allocate(alloc_list=worker_path_list)
								# print(datetime.datetime.now(), " New worker: ", new_worker)
								logging.error('6.5NewWorker {}'.format(new_worker))
								logging.error("SEND_EXPERIMENT 13")
								if new_worker == []:
									failed = True
									break
								else:
									del worker_path_list[last + i]
									worker_path_list += new_worker

						if failed:
							break

						last += role.no_workers
				else:
					logging.debug("SEND_EXPERIMENT 14")
					failed = True

				if failed:
					print(datetime.datetime.now(), exp.name, " Failed: not enough workers available!")
					logging.debug("SEND_EXPERIMENT 15")
					self.controller_client.task_del(task_now)

				else:
					for i in range(no_workers_total):
						logging.debug("SEND_EXPERIMENT 16 i: {}".format(i))
						self.controller_client.exp_ready_on_worker(exp.id, ready[i][0], ready[i][1])

					logging.debug("SEND_EXPERIMENT 17 exp_start: {}".format(exp.id))
					self.controller_client.exp_start(exp.id)

					logging.debug("SEND_EXPERIMENT 18. deleting current task.")
					self.controller_client.task_del(task_now)

					logging.debug("SEND_EXPERIMENT 19. done")

			elif task_cmd == COMMANDS.RECOVER_ACTOR:

				logging.info("RECOVER_ACTOR [1] task_args: %s" % str(task_args))
				worker = Worker.decode(task_args["worker"].decode('utf-8'))
				logging.debug("RECOVER_ACTOR [2] RecoverActor worker.hostname: {}".format(worker.hostname))
				exp_list = self.controller_client.worker_get_experiments(worker.hostname)
				logging.debug("RECOVER_ACTOR [3] RecoverActor exp_list: {}".format(exp_list))

				channel = None
				try:
					logging.info("RECOVER_ACTOR [4] creating a channel with: {}".format(worker.hostname))
					channel = Channel(worker.hostname, username=worker.username, pkey=worker.pkey,
									  password=worker.password, timeout=_timeout)
					remote_path = worker.get_remote_path()
					logging.debug("RECOVER_ACTOR [5] changing remote dir to: {}".format(remote_path))
					channel.chdir(remote_path)

					logging.debug("RECOVER_ACTOR [6] running stop command: {}".format(worker.get_command_stop()))
					channel.run(worker.get_command_stop())

					logging.debug("RECOVER_ACTOR [7] running start command: {}".format(worker.get_command_start()))
					stdout, stderr = channel.run(worker.get_command_start())

					stderr_str = stderr.read().strip()
					stdout_str = stdout.read().strip()

					logging.info("RECOVER_ACTOR [8] recovered: {}".format(worker.hostname))
					channel.close()

				except Exception as e:
					logging.info("RECOVER_ACTOR [9] Exception: {}".format(e))
					logging.info("RECOVER_ACTOR [9.1] Unable to connect with: {}".format(worker.hostname))

					if len(exp_list) == 0:
						logging.info("No experiment needed to recover. exp_list: {}".format(exp_list))

					else:
						worker_path_list = self.controller_client.worker_allocate(len(exp_list))
						logging.debug("RECOVER_ACTOR [10] worker_path_list: {}".format(worker_path_list))

						if worker_path_list:
							logging.debug("RECOVER_ACTOR [11] ")
							for i in range(len(exp_list)):
								logging.debug("RECOVER_ACTOR [12] i: {}".format(i))
								exp = exp_list[i]
								logging.debug("RECOVER_ACTOR [12] exp: {}".format(exp))
								rw = self.controller_client.worker_get(worker_path_list[i])
								logging.debug("RECOVER_ACTOR [13] rw.hostname: {}".format(rw.hostname))

								for role in exp.roles:
									logging.debug("RECOVER_ACTOR [13.1] role: {}".format(role))
									logging.debug("RECOVER_ACTOR [13.2] role.id: {} exp.actor.role_id: ".format(role.id, exp.actor.role_id))
									if role.id == exp.actor.role_id:
										logging.debug("RECOVER_ACTOR [14] role: {}".format(role))

										logging.info("RECOVER_ACTOR [15] creating a channel with: {}".format(rw.hostname))
										# Send experiment
										channel = Channel(hostname=rw.hostname, username=rw.username, password=rw.password,
														  pkey=rw.pkey, timeout=_timeout)
										# remote_path = "worker/experiments"
										remote_path = rw.get_remote_experiment_path()

										logging.debug(
											"RECOVER_ACTOR [16] changing dir to remote_path: {}".format(remote_path))
										channel.chdir(remote_path)

										if type(exp.name) is bytes:
											exp.name = exp.name.decode('utf-8')

										logging.info("RECOVER_ACTOR [16.2] making dir: {}".format(exp.name))
										channel.run("mkdir -p %s" % exp.name)

										logging.info("RECOVER_ACTOR [16.3] changing to dir {}".format(exp.name))
										channel.chdir(exp.name)

										logging.debug("RECOVER_ACTOR [17] exp.filename: {}".format(exp.filename))
										channel.put(_local_experiments_dir + exp.filename, exp.filename)

										logging.debug("RECOVER_ACTOR [18] unzipping filename: {}".format(exp.filename))
										channel.run("tar -xzf %s" % exp.filename)

										actor_id = self.controller_client.exp_create_actor(exp.id, rw.path, role.id,
																						   actor_path=exp.actor.path)
										channel.run(
											"echo \"parameters=%s\nexp_id=%s\nrole_id=%s\nactor_id=%s\nis_snapshot=%s\" > info.cfg" % (
											role.parameters, exp.id, role.id, actor_id, exp.is_snapshot))
										logging.debug("RECOVER_ACTOR [19] actor_id: {}".format(actor_id))
										self.controller_client.exp_ready_on_worker(exp.id, rw.path, actor_id)
										logging.debug("RECOVER_ACTOR [20]")
										channel.close()

							self.controller_client.worker_remove_experiments(worker.path)
							logging.debug("RECOVER_ACTOR [21]")
							self.controller_client.worker_add_disconnected(worker.hostname, 'LOST IDLE')
							logging.debug("RECOVER_ACTOR [22]")

						else:
							# ACTOR FAILURE!!
							# TODO: declare failed actor on experiment
							logging.debug("RECOVER ACTOR [23] FAILURE!")
							logging.error("Not enough workers available for reallocation to worker: {}".format(worker.hostname))

							# # AN ATTEMPT to the ABOVE todo
							# self.controller_client.worker_remove_experiments(worker.path)
							# logging.debug("[27]RecoverActor")
							# self.controller_client.worker_add_disconnected(worker.hostname, 'LOST BUSY')
							# logging.debug("[28]RecoverActor")

				self.controller_client.task_del(task_now)

			elif task_cmd == COMMANDS.NEW_EXPERIMENT:

				logging.info("NEW_EXPERIMENT task_args: %s" % str(task_args))
				exp = Experiment.decode(task_args["experiment"].decode('utf-8'))
				# logging.debug('Experiment_Literal_Debug: PASS !!!')
				exp.name = exp.name.replace(' ', '_')

				self.controller_client.exp_add(exp)
				self.controller_client.task_add(COMMANDS.SEND_EXPERIMENT, experiment=exp)
				self.controller_client.task_del(task_now)

			elif task_cmd == COMMANDS.NEW_WORKER:

				logging.info("NEW_WORKER task_args: %s" % str(task_args))
				# logging.debug(type(task_args["worker"]))
				# logging.debug('Literal_Debug: ' + task_args["worker"].decode('utf-8'))
				worker = Worker.decode(task_args["worker"].decode('utf-8'))
				logging.debug('Worker_Literal_Debug: PASS !!!')
				if not self.controller_client.worker_check(worker.hostname):

					try:
						# rmansilha channel = Channel(worker.hostname, username=worker.username, pkey = worker.pkey, password=worker.password, timeout=_timeout)
						# channel = Channel(worker.hostname, username=my_username, pkey=my_pkey, password=my_password, timeout=_timeout)
						channel = Channel(worker.hostname, username=worker.username, pkey=worker.pkey,
										  password=worker.password, timeout=_timeout)
						print(datetime.datetime.now(), worker.hostname, "is online")

						remote_path = worker.get_remote_path()
						channel.run("mkdir -p %s" % remote_path)
						# rafael# colocando endereco estatico
						# channel.run("echo \"server=%s:%s\nhostname=%s\" > %s/info.cfg" % (get_ip(), _controllerport, worker.hostname, remote_path))
						channel.run("echo \"server=%s:%s\nhostname=%s\" > %s/info.cfg" % (
						self.zookeeper_controller.get_ip_adapter(), _controllerport, worker.hostname, remote_path))

						# TODO#
						self.controller_client.worker_add(worker)
						# TODO#
						self.controller_client.task_add(COMMANDS.INSTALL_WORKER, worker=worker)

						channel.close()

					except Exception as e:
						# print(datetime.datetime.now(), worker.hostname, e)
						msg = "Exception while connecting to actor '{}': {} ".format(worker.hostname, e)
						logging.error(msg)
						# Unable to connect
						msg = "Actor '{}' will be removed due error.".format(worker.hostname)
						logging.info(msg)
						self.controller_client.worker_remove(worker)
				else:
					print(datetime.datetime.now(), worker.hostname, "hostname already registered!")
					# TODO: remove on final
					self.controller_client.task_add(COMMANDS.START_WORKER, worker=worker)

				self.controller_client.task_del(task_now)

			elif task_cmd == COMMANDS.INSTALL_WORKER:

				logging.info("INSTALL_WORKER task_args: %s" % str(task_args))

				worker = Worker.decode(task_args["worker"].decode('utf-8'))
				logging.debug('INSTALL_WORKER [1] worker: {}'.format(worker))

				# Install daemon
				try:
					logging.info('INSTALL_WORKER [3] creating channel...')
					# rmansilha channel = Channel(worker.hostname, username=worker.username, pkey = worker.pkey, password=worker.password, timeout=_timeout)
					# channel = Channel(worker.hostname, username=my_username, pkey=my_pkey, password=my_password, timeout=_timeout)
					channel = Channel(worker.hostname, username=worker.username, pkey=worker.pkey,
									  password=worker.password, timeout=_timeout)

					logging.info('INSTALL_WORKER [4] channel created.')

					# INSTALL PYTHON (+ MAKE + GCC)

					# TODO HACK: simplifies proccess in mininet, assuming the host is already ok
					if not "mininet" in worker.actor_id:
						logging.debug('INSTALL_WORKER [if.1] mininet not in worker.actor_id')

						stdout, stderr = channel.run("python3 -V")
						logging.debug('INSTALL_WORKER [if.2] python3 -V: {}'.format(stdout))

						stdout, stderr = channel.run("pip3 install --upgrade pip")
						logging.debug('INSTALL_WORKER [if.3] pip3 install: {}'.format(stdout))

					remote_path = worker.get_remote_path()
					logging.debug('INSTALL_WORKER [5] remote_path: {}'.format(remote_path))

					channel.run("mkdir -p %s/experiments" % remote_path)
					channel.chdir(remote_path)

					logging.debug('INSTALL_WORKER [6] creating _worklibtarfile: {}'.format(_worklibtarfile))
					create_worklib(_worklibtarfile)

					logging.debug('INSTALL_WORKER [7] transferring _worklibtarfile')
					channel.put(_worklibtarfile, _worklibtarfile)

					logging.debug('unzipping {}'.format(_worklibtarfile))
					channel.run("tar -xzf %s" % _worklibtarfile)

					logging.debug('INSTALL_WORKER [8] updating zookeeper')
					self.controller_client.worker_add_disconnected(worker.hostname, "INSTALLED", is_failure=False)
					logging.debug('INSTALL_WORKER [9] adding task COMMANDS.START_WORKER')
					self.controller_client.task_add(COMMANDS.START_WORKER, worker=worker)

				except Exception as e:
					logging.error("INSTALL_WORKER Exception - hostname: {} e: {}".format(worker.hostname, e))
					# logging.debug('python_install_excetion: [type:'+str(type(worker.hostname))+' data:'+str(worker.hostname)+' ]')
					logging.debug('INSTALL_WORKER [Exception] updating zookeeper')
					self.controller_client.worker_add_disconnected(worker.hostname, "NOT INSTALLED")

				logging.debug('INSTALL_WORKER [10] removing current task')
				self.controller_client.task_del(task_now)
				logging.debug('INSTALL_WORKER [11] DONE.')

			elif task_cmd == COMMANDS.START_WORKER:

				logging.info("START_WORKER task_args: %s" % str(task_args))
				worker = Worker.decode(task_args["worker"].decode('utf-8'))
				logging.debug('START_WORKER task_start_work: TRY p1')
				try:
					# rmansilha channel = Channel(worker.hostname, username=worker.username, pkey = worker.pkey, password=worker.password, timeout=_timeout)
					# channel = Channel(worker.hostname, username=my_username, pkey=my_pkey, password=my_password, timeout=_timeout)
					# Rafael#channel = Channel(worker.hostname, username=worker.username, pkey = (worker.pkey).decode('utf-8'), password=worker.password, timeout=_timeout)
					channel = Channel(worker.hostname, username=worker.username, pkey=worker.pkey,
									  password=worker.password, timeout=_timeout)
					remote_dir = worker.get_remote_path()
					channel.chdir(remote_dir)
					stdout, stderr = channel.run(worker.get_command_stop())
					# print datetime.datetime.now(), worker.hostname, "cmd: python %s stop" %(_worker_daemon), "stdout: ", stdout, "stderr: ", stderr
					logging.debug('START_WORKER task_start_work: TRY p2')
					#stdout, stderr = channel.run("python3 %s --id %s start" % (_worker_daemon, worker.actor_id))
					stdout, stderr = channel.run(worker.get_command_start())
					logging.debug('START_WORKER task_start_work: TRY p3 {}'.format(stdout))
					stderr_str = stderr.read().strip()
					stdout_str = stdout.read().strip()
					# print(datetime.datetime.now(), "\t", worker.hostname, "cmd: python %s start" %(_worker_daemon), "stdout: ", stdout_str, "stderr: ", stderr_str)
					logging.debug("START_WORKER {} {} cmd: {} start stdout: {} stderr: {}".format(datetime.datetime.now(),
																							 worker.hostname,
																							 worker.get_command_start(),
																							stdout_str,
																							 stderr_str))

					logging.info("START_WORKER daemon running at worker.hostname: {}".format(worker.hostname))

					channel.close()
					logging.debug('START_WORKER channel closed.')

				except Exception as e:
					logging.error('START_WORKER Exception: {} '.format(e))
					logging.error('START_WORKER Exception: adding disconnected ')
					self.controller_client.worker_add_disconnected(worker.hostname,
																   'LOST IDLE' if self.controller_client.worker_get_experiments(
																	   worker.hostname) == [] else 'LOST BUSY')

				logging.debug('START_WORKER deleting current task')
				self.controller_client.task_del(task_now)
				logging.debug('START_WORKER done.')

			elif task_cmd == COMMANDS.EXIT:
				self.controller_client.task_del(task_now)
				self.exit = True

			else:
				logging.error("ERROR: unknown task_cmd: {}".format(task_cmd))

	def run(self):
		logging.debug("Begin")
		logging.debug("Instantiating Controller Client")
		self.controller_client = ControllerClient(self.zookeeper_ip_port)
		logging.debug("Creating missing paths")
		self.controller_client.config_create_missing_paths()
		logging.debug("Setup watcher of new tasks")
		self.exit = False
		self.controller_client.watch_new_tasks(self.task_handler)  # RM
		# self.controller_client.watch_new_tasks(self.test_task_handler)  # RM
		logging.debug("Instantiating RPM sleep_seconds: {} zk_addr: {}".format(self.sleep_seconds, self.zookeeper_ip_port))
		rpm = RPM(self.sleep_seconds, self.zookeeper_ip_port)
		rpm.daemon = True

		while not self.exit:
			if not rpm.is_alive():
				logging.debug("Instantiating RPM sleep_seconds: {} zk_addr: {}".format(self.sleep_seconds,
																				   self.zookeeper_ip_port))
				rpm = RPM(self.sleep_seconds, self.zookeeper_ip_port)
				rpm.daemon = True
				logging.debug("Starting RPM")
				rpm.start()

			time.sleep(self.sleep_seconds)

		logging.debug("Terminating RPM")
		rpm.terminate()
		self.controller_client.config_stop()


class Director(DirectorDaemon):

	def __init__(self):
		self.zookeeper_controller = ZookeeperController()
		self.controller_client = None  # self.zookeeper_controller.controller_client
		self.sleep_seconds = None
		self.zookeeper_ip_port = self.zookeeper_controller.zookeeper_ip_port


def cmd(option):
	cmd_array = ['python3', __file__, option]
	subprocess.call(cmd_array)


def stop():
	cmd('stop')


def status():
	cmd('status')


def start():
	cmd('start')


def restart():
	cmd('restart')


def main():
	# arguments
	parser = argparse.ArgumentParser(description='Daemon Director')

	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

	help_msg = "unique id (str), required for running multiple daemons on the host"
	parser.add_argument("--id", "-i", help=help_msg, default="default", type=str)

	help_msg = "loop sleep seconds (int)"
	parser.add_argument("--sleep", "-s", help=help_msg, default=DEFAULT_SLEEP_SECONDS, type=int)

	cmd_choices = ['foreground', 'start', 'stop', 'restart', 'status']
	parser.add_argument('cmd', choices=cmd_choices)

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
	logging.info("\t unique id     : %s" % args.id)
	logging.info("\t sleep secs    : %s" % args.sleep)
	logging.info("\t command option: %s" % args.cmd)
	logging.info("")

	logging.info("FILES")
	logging.info("---------------------")

	if args.cmd == 'foreground':
		logging.info("\t pid_file      : None (foreground process) ")
		logging.info("\t stdout        : None (foreground process)")
		logging.info("\t stderr        : None (foreground process)")
		logging.info("")
		director = Director()
		director.set_sleep_seconds(args.sleep)
		director.run()

	else:
		pid_file = "/tmp/daemon_director_%s.pid" % args.id
		stdout = "/tmp/daemon_director_%s.stdout" % args.id
		stderr = "/tmp/daemon_director_%s.stderr" % args.id

		logging.info("\t pid_file      : %s" % pid_file)
		logging.info("\t stdout        : %s" % stdout)
		logging.info("\t stderr        : %s" % stderr)
		logging.info("")

		zookeeper_controller = ZookeeperController()
		director_daemon = DirectorDaemon(pidfile=pid_file, stdout=stdout, stderr=stderr)
		logging.debug("Instatianting zookeeper controller")
		director_daemon.set_sleep_seconds(args.sleep)

		# process input parameters
		if args.cmd == 'start':
			logging.info("Starting director daemon (ensemble)")
			director_daemon.start()

			director_daemon_pid = director_daemon.getpid()

			if not director_daemon_pid:
				logging.info("Unable to run director daemon (ensemble)")
			else:
				logging.info("Director daemon is running [PID=%d]" % director_daemon_pid)

		elif args.cmd == 'stop':
			logging.info("Stopping director daemon (ensemble)")
			director_daemon.stop()

		elif args.cmd == 'restart':
			logging.info("Restarting director daemon (ensemble)")
			director_daemon.restart()

		elif args.cmd == 'status':
			director_daemon_pid = director_daemon.getpid()

			if not director_daemon_pid:
				logging.info("Director daemon (id='%s') isn't running" % (args.id))
			else:
				logging.info("Director daemon (id='%s') is running [PID=%d]" % (args.id, director_daemon_pid))


if __name__ == '__main__':
	sys.exit(main())
