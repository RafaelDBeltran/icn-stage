#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

#
#	@author: Nelson Antonio Antunes Junior
#	@email: nelson.a.antunes at gmail.com
#	@date: (DD/MM/YYYY) 24/01/2017
#commit
import argparse
import sys, socket, time, multiprocessing, subprocess, signal
import datetime
#TODO#
from zookeeper_controller import ZookeeperController

sys.path.append(r'~/myRuns/modules')
import logging

from modules.conlib.controller_client import *
from modules.conlib.remote_access import Channel

from modules.extralib.daemon import Daemon
from modules.model.worker import Worker
from modules.model.experiment import Experiment
from modules.model.role import Role
import json
import tarfile
import os

'''
data = json.load(open('config.json'))
my_adapter_ip = ConfigHelper(data["zookeeper_adapter"])
'''
LOG_LEVEL = logging.DEBUG
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_SLEEP_SECONDS = 30


_controllerport = "2181"
_pyvers = "3.6.9"
_timeout = 30
_worker_daemon = "daemon_worker.py"
_worklibtarfile = "worklib.tar.gz"


#TODO#
# _local_experiments_dir = os.path.expanduser("~/controller/experiments/")
#_local_experiments_dir = os.path.expanduser("/home/rafael/Documents/ExtendEasyExp/")
_local_experiments_dir = os.path.expanduser("./")


def create_worklib(output_file_):

	# setup
	#modules_source_path = "./modules/"
	worklib_source_path = "./modules/worklib/"
	extralib_source_path = "./modules/extralib/"

	# creates tar file
	tar_file = tarfile.open(output_file_, "w:gz")

	# add main file
	tar_file.add("%s" % (_worker_daemon))

	# add modules
	current_dir = os.getcwd()
	#os.chdir(modules_source_path)
	for d in [worklib_source_path, extralib_source_path]:

		for f in os.listdir(d):
			file = "%s/%s" % (d, f)
			logging.debug("File: %s" % file)
			if file.endswith('.py'):
				logging.debug("adding %s"%file)
				tar_file.add("%s" % (file))
			else:
				logging.debug("skiping %s" % file)
				#logging.debug(file)

	# close file
	tar_file.close()
	os.chdir(current_dir)


def get_ip():
	return [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]


_realocate_timeout = 240
_restart_timeout = _realocate_timeout/2


# RPM = Resource Pool Manager
class RPM(multiprocessing.Process):

	def __init__(self):
		super().__init__()
		self.sleep_seconds = DEFAULT_SLEEP_SECONDS
		self.controller_client = None

	def set_sleep_seconds(self, sleep_seconds):
		self.sleep_seconds = sleep_seconds

	def set_controller_client(self, controller_client):
		self.controller_client = controller_client

	def run(self):

		exit = False

		workers = self.controller_client.worker_get_all()
		workers_disconnected = set([x for x in workers if x.status != 'BUSY' or x.status != 'IDLE'])
		workers = set(workers)
		starting_time = time.time()
		last= starting_time
		while not exit:
			now = time.time()
			try:
				with open("rpm_activity.log","w+") as fa:
					print("%16s, \t%50s, \t%13s, \t%24s, \t%24s" %('ACTIVE_TIME', 'HOSTNAME', 'STATUS', 'LAST_CALL', 'WHEN_DISCONNECT'), file=fa)

					for worker in sorted(self.controller_client.worker_get_all(), key=lambda x: x.hostname):

						if worker.status == 'BUSY' or worker.status == 'IDLE':
							if worker.hostname in workers_disconnected or not (worker in workers):
								self.controller_client.worker_update_connection_time(worker.path, now)
								workers_disconnected.discard(worker.hostname)

						else:
							logging.debug("[1]RecoverActor {}".format(workers_disconnected))
							workers_disconnected.add(worker.hostname)
							if worker.status == 'NEW LOST BUSY' or worker.status == 'LOST BUSY':
								if not worker.actors:
									break
								with open('failures_recov.txt','a+') as fi:
									print(time.time(), worker.hostname, worker.actors, file=fi)
								logging.debug("[2]RecoverActor")
								self.controller_client.worker_add_disconnected(worker.hostname, 'RECOVERING')
								self.controller_client.task_add(COMMANDS.RECOVER_ACTOR, worker=worker)
								logging.debug("[3]RecoverActor")
							elif worker.status == 'LOST IDLE' or worker.status == 'NEW LOST IDLE':
								logging.debug("[4]RecoverActor")
								self.controller_client.worker_add_disconnected(worker.hostname, 'RESTARTING')
								logging.debug("[5]RecoverActor")
								self.controller_client.task_add(COMMANDS.START_WORKER, worker=worker)
								logging.debug("[6]RecoverActor")

						workers.add(worker)

						dcnx_time = ''
						if worker.disconnection_time != 0:
							dcnx_time = time.ctime(worker.disconnection_time)

						last_login = ''
						if worker.connection_time != 0:
							last_login = time.ctime(worker.connection_time)

						print("%16f, \t%50s, \t%13s, \t%24s, \t%24s" %(worker.active_time, worker.hostname, worker.status, last_login, dcnx_time), file=fa)

			except Exception as e:

				#TODO: mensagem mais profissional e com menos hack
				#print("download version1")
				#print("wget https://downloads.apache.org/zookeeper/zookeeper-3.6.0/apache-zookeeper-3.6.0-bin.tar")

				with open("rpm_output.log","a+") as fo:
					print(time.time(), worker.hostname, " exception: ", e, file=fo)
			last = now
			time.sleep(self.sleep_seconds)
		#TODO
		#self.controller_client.close()


class DirectorDaemon(Daemon):

	def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
		super().__init__(pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null')
		self.zookeeper_controller = ZookeeperController()
		self.sleep_seconds = None
		self.controller_client = None
		self.zookeeper_ip_port = self.zookeeper_controller.zookeeper_ip_port

	def set_sleep_seconds(self, sleep_seconds):
		self.sleep_seconds = sleep_seconds
		logging.debug("done.")

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
						tries = len(worker_path_list) # number of possible allocate workers
						logging.debug("SEND_EXPERIMENT 6 %s" % remaining)
						i = 0
						#worker_path_list = [new_path.decode('utf-8') for new_path in worker_path_list]
						while remaining and tries > 0:
							try:
								logging.debug("SEND_EXPERIMENT 6.5  {}".format(worker_path_list[last+i]))
								worker = self.controller_client.worker_get(worker_path_list[last + i])

								logging.debug("SEND_EXPERIMENT 7")
								logging.info(" connecting to %s " % worker.hostname)
								channel = Channel(hostname=worker.hostname, username=worker.username, password=worker.password, pkey=worker.pkey, timeout=_timeout)

								remote_path = worker.get_remote_experiment_path()
								logging.debug("SEND_EXPERIMENT 7.1 changing dir to {} ".format(remote_path))
								channel.chdir(remote_path)

								logging.info("SEND_EXPERIMENT 7.2 making dir {}".format(exp.name))
								channel.mkdir(exp.name)

								logging.info("SEND_EXPERIMENT 7.3 changing to dir {}".format(exp.name))
								channel.chdir(exp.name)

								logging.debug("SEND_EXPERIMENT 8 file: {} to: {}".format(_local_experiments_dir+exp.filename, remote_path))
								channel.put(_local_experiments_dir+exp.filename, exp.filename)

								logging.debug("SEND_EXPERIMENT 9 unzipping file {}".format(exp.filename))
								channel.run("tar -xzf %s" % exp.filename)
								logging.debug("SEND_EXPERIMENT 10 unzipping done.")

								actor_id = self.controller_client.exp_create_actor(exp.id, worker.path, role.id)
								channel.run("echo \"parameters=%s\nexp_id=%s\nrole_id=%s\nactor_id=%s\nis_snapshot=%s\" > info.cfg" % (role.parameters, exp.id, role.id, actor_id, exp.is_snapshot))
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
									del worker_path_list[last+i]
									worker_path_list += new_worker

						if failed:
							break

						last += role.no_workers
				else:
					logging.debug("SEND_EXPERIMENT 14")
					failed = True

				if failed:
					print(datetime.datetime.now(), exp.name," Failed: not enough workers available!")
					logging.debug("SEND_EXPERIMENT 15")
					self.controller_client.task_del(task_now)

				else:
					for i in range(no_workers_total):
						self.controller_client.exp_ready_on_worker(exp.id, ready[i][0], ready[i][1])
						logging.debug("SEND_EXPERIMENT 16")

					self.controller_client.exp_start(exp.id)

					print(datetime.datetime.now(), exp.name, "run all!")

					self.controller_client.task_del(task_now)
					logging.debug("SEND_EXPERIMENT 17")

			elif task_cmd == COMMANDS.RECOVER_ACTOR:

				logging.info("RECOVER_ACTOR task_args: %s"%str(task_args))
				logging.debug("RECOVER_ACTOR [1] RecoverActor")
				worker = Worker.decode(task_args["worker"].decode('utf-8'))
				logging.debug("RECOVER_ACTOR [2] RecoverActor")
				exp_list = self.controller_client.worker_get_experiments(worker.hostname)
				logging.debug("RECOVER_ACTOR [3]RecoverActor")
				channel = None

				try:
					logging.info("RECOVER_ACTOR [4] connecting to {}".format(worker.hostname))

					#rmansilha channel = Channel(worker.hostname, username=worker.username, pkey = worker.pkey, password=worker.password, timeout=_timeout)
					# channel = Channel(worker.hostname, username=my_username, pkey=my_pkey, password=my_password, timeout=_timeout)
					channel = Channel(worker.hostname, username=worker.username, pkey=worker.pkey, password=worker.password, timeout=_timeout)
					remote_path = worker.get_remote_path()
					channel.chdir(remote_path)
					channel.run("python3 %s stop" % (_worker_daemon))
					stdout, stderr = channel.run("python3 %s restart" % (_worker_daemon))
					stderr_str = stderr.read().strip()
					stdout_str = stdout.read().strip()
					print(datetime.datetime.now(), "\t", worker.hostname, "cmd: python3 %s restart"%(_worker_daemon), "stdout: ", stdout_str, "stderr: ", stderr_str)

					print(datetime.datetime.now(), "\t", worker.hostname, "daemon recovered")
					logging.debug("RECOVER_ACTOR [5] RecoverActor")
					channel.close()

				except:
					print(datetime.datetime.now(),"\t", worker.hostname, 'unable to connect')
					logging.debug("[11]RecoverActor")
					worker_path_list = self.controller_client.worker_allocate(len(exp_list))
					logging.debug("[12]RecoverActor")
					if worker_path_list:
						logging.debug("[13]RecoverActor")
						for i in range(len(exp_list)):
							logging.debug("[14]RecoverActor")
							exp = exp_list[i]
							w = self.controller_client.worker_get(worker_path_list[i])
							logging.debug("[15]RecoverActor")
							for role in exp.roles:
								if role.id == exp.actor.role_id:
									logging.debug("[16]RecoverActor")
									print(datetime.datetime.now(), w.hostname, "connecting")

									#Send experiment
									#rmansilha channel = Channel(hostname=w.hostname, username=w.username, password=w.password, pkey=w.pkey, timeout=_timeout)
									# channel = Channel(hostname=w.hostname, username=my_username, password=my_password, pkey=my_pkey, timeout=_timeout)
									channel = Channel(hostname=w.hostname, username=w.username, password=w.password, pkey=w.pkey, timeout=_timeout)
									#remote_path = "worker/experiments"
									remote_path = worker.get_remote_experiment_path()
									channel.chdir(remote_path)
									logging.debug("[17]RecoverActor")
									channel.run("mkdir -p %s" % exp.name)
									channel.chdir(exp.name)
									logging.debug("[18]RecoverActor")
									print(datetime.datetime.now(), w.hostname, "sending experiment")

									channel.put(_local_experiments_dir+exp.filename, exp.filename)
									logging.debug("[19]RecoverActor")
									#all experiments files must be gzipped
									logging.debug('expFilename ')
									logging.debug('expFilename {}'.format(_local_experiments_dir+exp.filename))
									logging.debug("[20]RecoverActor")
									channel.run("tar -xzf %s" % exp.filename)
									logging.debug("[21]RecoverActor")
									logging.debug('expFilename ')
									actor_id = self.controller_client.exp_create_actor(exp.id, w.path, role.id, actor_path=exp.actor.path)
									channel.run("echo \"parameters=%s\nexp_id=%s\nrole_id=%s\nactor_id=%s\nis_snapshot=%s\" > info.cfg" % (role.parameters, exp.id, role.id, actor_id, exp.is_snapshot))
									logging.debug("[22]RecoverActor")
									self.controller_client.exp_ready_on_worker(exp.id, w.path, actor_id)
									logging.debug("[23]RecoverActor")
									channel.close()


						self.controller_client.worker_remove_experiments(worker.path)
						logging.debug("[24]RecoverActor")
						self.controller_client.worker_add_disconnected(worker.hostname, 'LOST IDLE')
						logging.debug("[25]RecoverActor")

					else:
						#ACTOR FAILURE!!
						#TODO: declare failed actor on experiment
						logging.debug("[26]RecoverActor")
						print(datetime.datetime.now(), worker.hostname, "Not enough workers available for reallocation!")

						#AN ATEMPTY to the ABOVE todo
						self.controller_client.worker_remove_experiments(worker.path)
						logging.debug("[27]RecoverActor")
						self.controller_client.worker_add_disconnected(worker.hostname, 'LOST BUSY')
						logging.debug("[28]RecoverActor")

				self.controller_client.task_del(task_now)

			elif task_cmd == COMMANDS.NEW_EXPERIMENT:

				logging.info("NEW_EXPERIMENT task_args: %s" % str(task_args))
				exp = Experiment.decode(task_args["experiment"].decode('utf-8'))
				# logging.debug('Experiment_Literal_Debug: PASS !!!')
				exp.name = exp.name.replace(' ','_')

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
						#rmansilha channel = Channel(worker.hostname, username=worker.username, pkey = worker.pkey, password=worker.password, timeout=_timeout)
						# channel = Channel(worker.hostname, username=my_username, pkey=my_pkey, password=my_password, timeout=_timeout)
						channel = Channel(worker.hostname, username=worker.username, pkey=worker.pkey, password=worker.password, timeout=_timeout)
						print(datetime.datetime.now(), worker.hostname,"is online")

						remote_path = worker.get_remote_path()
						channel.run("mkdir -p %s" %remote_path)
						#rafael# colocando endereco estatico
						# channel.run("echo \"server=%s:%s\nhostname=%s\" > %s/info.cfg" % (get_ip(), _controllerport, worker.hostname, remote_path))
						channel.run("echo \"server=%s:%s\nhostname=%s\" > %s/info.cfg" % (self.zookeeper_controller.get_ip_adapter(),_controllerport, worker.hostname, remote_path))

						#TODO#
						self.controller_client.worker_add(worker)
						#TODO#
						self.controller_client.task_add(COMMANDS.INSTALL_WORKER, worker=worker)

						channel.close()

					except Exception as e:
						#print(datetime.datetime.now(), worker.hostname, e)
						msg = "Exception while connecting to actor '{}': {} ".format(worker.hostname, e)
						logging.error(msg)
						#Unable to connect
						msg = "Actor '{}' will be removed due error.".format(worker.hostname)
						logging.info(msg)
						self.controller_client.worker_remove(worker)
				else:
					print(datetime.datetime.now(), worker.hostname, "hostname already registered!")
					#TODO: remove on final
					self.controller_client.task_add(COMMANDS.START_WORKER, worker=worker)

				self.controller_client.task_del(task_now)

			elif task_cmd == COMMANDS.INSTALL_WORKER:

				logging.info("INSTALL_WORKER task_args: %s" % str(task_args))

				worker = Worker.decode(task_args["worker"].decode('utf-8'))
				logging.debug('INSTALL_WORKER [1]')
				#Install daemon

				try:
					logging.debug('INSTALL_WORKER [2]')

					logging.info(str(datetime.datetime.now()) +' '+ str( worker.hostname) +" connecting")
					logging.debug('INSTALL_WORKER [2] logging.info_OK')
					#rmansilha channel = Channel(worker.hostname, username=worker.username, pkey = worker.pkey, password=worker.password, timeout=_timeout)
					# channel = Channel(worker.hostname, username=my_username, pkey=my_pkey, password=my_password, timeout=_timeout)
					channel = Channel(worker.hostname, username=worker.username, pkey = worker.pkey, password=worker.password, timeout=_timeout)

					logging.debug('INSTALL_WORKER [3] Install_Worker_Literal_Debug: TRY p2')

					#INSTALL PYTHON (+ MAKE + GCC)

					print(datetime.datetime.now(), worker.hostname,"downloading dependencies")
					#TODO
					#channel.run("sudo yum install -y --nogpgcheck openssl-devel libffi-devel")
					logging.debug('INSTALL_WORKER [3] Install_Worker_Literal_Debug: TRY p3')
					#Python version output goes to the stderr interface (y tho?)

					#stdout,stderr = channel.run("python3 -V")
					stdout,stderr = channel.run("python3 -V")

					logging.debug('INSTALL_WORKER [4] Install_Worker_Literal_Debug: TRY p4')

					#Rafael#vers = stderr.read().strip()
					stdout,stderr = channel.run("pip install --upgrade pip")
					# version = stdout.read().strip().decode('utf-8')
					# version = version.split(' ', 1)
					#logging.debug('Install_Worker_Literal_Debug: TRY p4.2 '+ str(stdout.read().strip()))

					#Rafael# if vers.split(' ')[-1].encode() < _pyvers:
					# if version[1] < _pyvers:
					# 	logging.debug('CompareOk')
					# 	try:
					# 		pass
							#TODO #Rafael
							# print(datetime.datetime.now(), worker.hostname,"installing Python %s + pip [+ gcc + make] (actual version = %s)" % (_pyvers,version[1]))
							# logging.debug('Install_Worker_Literal_Debug: TRY p5')
							# channel.run("sudo yum update")
							# channel.run("sudo yum install -y --nogpgcheck make gcc")
							# channel.run("sudo yum install -y --nogpgcheck gdbm zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel")
							# channel.run("sudo yum install -y --nogpgcheck redhat-rpm-config libffi-devel python-devel openssl-devel")

							#channel.run("wget https://www.python.org/ftp/python/%s/Python-%s.tgz" % (_pyvers,_pyvers))

							# if not os.path.isfile("Python-%s.tgz"%_pyvers):
							# 	print("Python-%s.tgz not found! downloading... "%_pyvers, end=' ')
							# 	os.system("wget https://www.python.org/ftp/python/%s/Python-%s.tgz"%(_pyvers,_pyvers))
							# 	print(" done.")
							# 	logging.debug('Install_Worker_Literal_Debug: TRY p6')

							# if not os.path.isfile("Python-%s.tgz"%_pyvers):
							# 	logging.debug('Install_Worker_Literal_Debug: TRY p7')
							# 	print("")
							# 	print("ERROR: could not download https://www.python.org/ftp/python/%s/Python-%s.tgz" % (_pyvers,_pyvers))

							# print(datetime.datetime.now(), worker.hostname," uplooading Python-%s.tgz"%_pyvers)
							# channel.put("Python-%s.tgz"%_pyvers, "Python-%s.tgz"%_pyvers)
							# logging.debug('Install_Worker_Literal_Debug: TRY p8')
							# print(datetime.datetime.now(), worker.hostname," unziping Python-%s.tgz"%_pyvers)
							# channel.run("tar -xzf Python-%s.tgz" % _pyvers)
							# logging.debug('Install_Worker_Literal_Debug: TRY p9')
							# channel.chdir("~/Python-%s" % _pyvers)
							# print(datetime.datetime.now(), "configuring (cd ~/Python-%s ; ./configure --with-ensurepip=yes) " % _pyvers)
							# channel.run("./configure --with-ensurepip=yes")
							# print(datetime.datetime.now(), worker.hostname, " make")
							# channel.run("make")
							# print(datetime.datetime.now(), worker.hostname," sudo make install")
							# channel.run("sudo make install")
							# print(datetime.datetime.now(), worker.hostname, " sudo pip install --upgrade pip")
							# channel.run("sudo pip install --upgrade pip")
							# channel.chdir("~/")
							# logging.debug('Install_Worker_Literal_Debug: TRY p10')
						# except:
						# 	logging.debug('Error in the Python install')
						#channel.run("rm -rf Python-%s*" % _pyvers)
					logging.debug('INSTALL_WORKER [5] Install_Worker_Literal_Debug: TRY p8')
					#Rafael#
					# _, stderr = channel.run("python -V")
					# vers = stderr.read().strip()
					# if vers.split(' ')[-1] >= _pyvers:
					# if version[1] >= _pyvers:
					# 	print(datetime.datetime.now(), worker.hostname, "python is up-to-date")
					# else:
						# print(datetime.datetime.now(), worker.hostname, "python is NOT up-to-date: ", version)

					print(datetime.datetime.now(), worker.hostname, "sending daemon and API")

					remote_path = worker.get_remote_path()
					logging.debug('Install_Worker_Literal_Debug: TRY p9')
					channel.run("mkdir -p %s/experiments" % remote_path)
					logging.debug('Install_Worker_Literal_Debug: TRY p10')
					channel.chdir(remote_path)

					create_worklib(_worklibtarfile)
					logging.debug('Install_Worker_Literal_Debug: TRY p11')

					channel.put(_worklibtarfile, _worklibtarfile)
					#channel.put(_worklibtarfile, remote_path)
					logging.debug('Install_Worker_Literal_Debug: TRY p12 {}'.format(_worklibtarfile))
					channel.run("tar -xzf %s"%_worklibtarfile)
					logging.debug('Install_Worker_Literal_Debug: TRY p13')
					self.controller_client.worker_add_disconnected(worker.hostname, "INSTALLED", is_failure=False)
					logging.debug('Install_Worker_Literal_Debug: TRY p14')
					self.controller_client.task_add(COMMANDS.START_WORKER, worker=worker)
					logging.debug('Install_Worker_Literal_Debug: TRY p15')

				except Exception as e:
					print(datetime.datetime.now(), worker.hostname, e)
					#logging.debug('python_install_excetion: [type:'+str(type(worker.hostname))+' data:'+str(worker.hostname)+' ]')
					self.controller_client.worker_add_disconnected(worker.hostname, "NOT INSTALLED")

				self.controller_client.task_del(task_now)

			elif task_cmd == COMMANDS.START_WORKER:

				logging.info("START_WORKER task_args: %s" % str(task_args))
				worker = Worker.decode(task_args["worker"].decode('utf-8'))
				logging.debug('task_start_work: TRY p1')
				try:
					#rmansilha channel = Channel(worker.hostname, username=worker.username, pkey = worker.pkey, password=worker.password, timeout=_timeout)
					# channel = Channel(worker.hostname, username=my_username, pkey=my_pkey, password=my_password, timeout=_timeout)
					#Rafael#channel = Channel(worker.hostname, username=worker.username, pkey = (worker.pkey).decode('utf-8'), password=worker.password, timeout=_timeout)
					channel = Channel(worker.hostname, username=worker.username, pkey=worker.pkey, password=worker.password, timeout=_timeout)
					remote_dir = worker.get_remote_path()
					channel.chdir(remote_dir)
					stdout, stderr = channel.run("python3 %s --id %s stop" % (_worker_daemon, worker.actor_id))
					#print datetime.datetime.now(), worker.hostname, "cmd: python %s stop" %(_worker_daemon), "stdout: ", stdout, "stderr: ", stderr
					logging.debug('task_start_work: TRY p2')
					stdout, stderr = channel.run("python3 %s --id %s start" % (_worker_daemon, worker.actor_id))
					logging.debug('task_start_work: TRY p3 {}'.format(stdout))
					stderr_str = stderr.read().strip()
					stdout_str = stdout.read().strip()
					#print(datetime.datetime.now(), "\t", worker.hostname, "cmd: python %s start" %(_worker_daemon), "stdout: ", stdout_str, "stderr: ", stderr_str)
					logging.debug("{} {} cmd: python3 {} start stdout: {} stderr: {}".format(datetime.datetime.now(),worker.hostname,_worker_daemon,stdout_str,stderr_str))
					logging.debug('task_start_work: TRY p4')
					print(datetime.datetime.now(), "\t", worker.hostname, "daemon running")

					channel.close()
					logging.debug('task_start_work: TRY p5')

				except Exception as e:
					logging.debug('task_start_work: TRY p6')
					print(datetime.datetime.now(), worker.hostname, e)
					self.controller_client.worker_add_disconnected(worker.hostname, 'LOST IDLE' if self.controller_client.worker_get_experiments(worker.hostname) == [] else 'LOST BUSY')
					logging.debug('task_start_work: TRY p7')
				logging.debug('task_start_work: TRY p8')
				self.controller_client.task_del(task_now)
				logging.debug('task_start_work: TRY p9')

			elif task_cmd == COMMANDS.EXIT:
				self.controller_client.task_del(task_now)
				self.exit = True
			else:
				logging.info("ERRO")

	def run(self):
		logging.debug("Begin")
		logging.debug("Instatiating Controller Client")
		self.controller_client = ControllerClient(self.zookeeper_ip_port)
		logging.debug("Creating missing paths")
		self.controller_client.config_create_missing_paths()
		logging.debug("Setup watcher of new tasks")
		self.exit = False
		self.controller_client.watch_new_tasks(self.task_handler) # RM
		#self.controller_client.watch_new_tasks(self.test_task_handler)  # RM
		logging.debug("Instanting RPM")
		rpm = RPM()
		logging.debug("Setup RPM Controller Client")
		rpm.set_controller_client(self.controller_client)
		rpm.daemon = True

		while not self.exit:

			if not rpm.is_alive():
				rpm = RPM()
				rpm.set_controller_client(self.controller_client)
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
		self.controller_client = None #self.zookeeper_controller.controller_client
		self.sleep_seconds = None


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
		logging.info("\t pid_file      : None (foreground process) " )
		logging.info("\t stdout        : None (foreground process)" )
		logging.info("\t stderr        : None (foreground process)" )
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