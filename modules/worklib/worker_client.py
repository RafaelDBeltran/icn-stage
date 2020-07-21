#
#   @author: Nelson Antonio Antunes Junior
#   @email: nelson.a.antunes at gmail.com
#   @date: (DD/MM/YYYY) 27/01/2017
from modules.worklib.snapshot import Snapshot
from kazoo.client import *
import kazoo, traceback, threading, imp, os, time, subprocess
import sys
import logging

class Printer:
	def __init__(self):
		self.fds = {}
		self.default = open('file_not_found.txt', 'a+', 1)

	def write(self, value):
		try:
			self.fds[threading.currentThread()].write(value)
		except:
			self.default.write(value)

	def add(self, fd):
		self.fds[threading.currentThread()] = fd


# STATIC PATHS
class PATHS(object):
	CONNECTED_FREE = "/connected/free_workers"
	CONNECTED_BUSY = "/connected/busy_workers"
	DISCONNECTED = '/disconnected/workers'
	REGISTERED_WORKERS = "/registered/workers/"


class Experiment(object):

	def printd(self, msg):
		f = open("wc_log.txt", "a")
		f.write("%s\n"%msg)
		f.close()

	def __init__(self, exp_path, exp_name, exp_parameters, exp_actor_id, is_snapshot):
		if type(exp_path) is bytes:
			self.path = exp_path.decode('utf-8')
		else:
			self.path = exp_path
		if type(exp_name) is bytes:
			self.name = exp_name.decode('utf-8')
		else:
			self.name = exp_name
		if type(exp_parameters) is bytes:
			self.parameters = exp_parameters.decode('utf-8')
		else:
			self.parameters = exp_parameters
		self.popen = None
		if type(exp_actor_id) is bytes:
			self.actor_id = exp_actor_id.decode('utf-8')
		else:
			self.actor_id = exp_actor_id
		self.worker_torun_id = ''
		if type(is_snapshot) is bytes:
			self.is_snapshot = is_snapshot.decode('utf-8')
		else:
			self.is_snapshot = is_snapshot
		self.snapshot = Snapshot()


	# def get_python_script_position(self):
	# 	i = 0
	# 	for (p in self.parameters):
	# 		if ".py" in p:
	# 			return i
	#
	# 		i +=1

	def run(self, wclient):
		if self.is_snapshot:
			try:
				exp_mod = imp.load_source('Actor', 'experiments/%s/Actor.py' % self.name)
				self.snapshot = exp_mod.Actor()
				self.snapshot.config(wclient, self.path, self.actor_id, 'experiments/%s/' % self.name)
				self.popen = threading.Thread(target=self.snapshot.start,
											  args=(self.parameters, 'experiments/%s/%s.' % (self.name, self.name)))
				self.popen.daemon = True
				self.popen.start()
			except:
				traceback.print_exc()
				self.snapshot.poll = -2
		else:
			try:
				#self.popen = subprocess.Popen(["cd", "experiments/%s;" % self.name, "%s" % self.parameters, "1>%s.out" % self.name,"2>%s.err" % self.name])
				param = self.parameters.split(" ")
				#param = shlex.split(self.parameters)
				cwd = "%s/experiments/%s/" % (os.getcwd(), self.name)
				self.popen = subprocess.Popen(param, cwd=cwd)
				self.poll = self.popen.poll()
				#self.printd("run poll: "+ str(self.popen.poll()))
			except:
				#self.printd("except while popen")
				self.poll = -2

	def get_main_script(self):
		#return shlex.split(self.parameters)[1]
		return self.parameters.split(" ")[1]

	def ps_based_is_running(self):
		script = self.get_main_script()
		cmd = "ps aux | grep %s | grep -v grep "%script
		#self.printd("ps_based_is_running - cmd " + cmd)
		#r = subprocess.call(cmd, shell=True)
		r = subprocess.getoutput(cmd)
		#self.printd("ps_based_is_running - r " + r)
		return r != ""

	def is_running(self):
		if self.is_snapshot:
			if self.popen:
				return self.popen.is_alive()
			else:
				return False
		else:
			#self.printd("is running: " + str(self.popen.poll()))
			return self.ps_based_is_running()
			#return (self.popen.poll() is None) or (self.popen.poll() == 0)

	def is_finished(self):
		if self.is_snapshot:
			return not (self.snapshot.poll is None)
		else:
			#self.printd("is finished: " + str(self.popen.poll() ))
			#return not ((self.popen.poll() is None) or (self.popen.poll() == 0))
			return not self.ps_based_is_running()

	def is_started(self):
		#self.printd("is started: " + str(self.popen))
		return self.popen


class WorkerClient(object):

	def printd(self, msg):
		f = open("wc_log.txt", "a")
		f.write("%s\n"%msg)
		f.close()

	def __init__(self, zk_addr, worker_hostname=''):
		logging.debug('#Here1')
		self.current_experiments = []  # Experiment objects
		self.zk = KazooClient(zk_addr, connection_retry=kazoo.retry.KazooRetry(max_tries=-1, max_delay=250))
		self.zk_addr = zk_addr
		self.hostname = worker_hostname
		self.worker_path = PATHS.REGISTERED_WORKERS + worker_hostname
		self.reregister = True
		self.busy = None
		self.connection = None
		self.connection_timeout = 0
		self.zk.add_listener(lambda x: os._exit(1) if x == KazooState.LOST else None)
		self.zk.start()

	def connected(self):
		logging.debug('#Here2')
		if self.connection is None:
			return False
		if self.zk.exists(self.connection):
			return True
		self.connection = None
		return False

	@staticmethod
	def load_config_file(filepath):
		logging.debug('#Here3')
		cfg = {}
		f = open(filepath, "r")
		for l in f.readlines():
			opt, arg = l.split("=")
			cfg[opt] = arg[:-1]
		return cfg

	def worker_active_time_uptade(self, adding_time):
		logging.debug('#Here4')
		active_time = float(self.zk.get("%s/active_time" % self.worker_path)[0])
		self.zk.set("%s/active_time" % self.worker_path, value=str(active_time + adding_time).encode())

	def worker_keep_alive(self, time, busy=False):
		logging.debug('#Here4')
		connected = False
		try:
			connected = self.connected()
		except:
			pass

		if connected:
			self.worker_active_time_uptade(time)

		if (not self.connection) or busy != self.busy:

			connection_path = "%s/%s" % (PATHS.CONNECTED_BUSY if busy else PATHS.CONNECTED_FREE, self.hostname)
			delete_path = "%s/%s" % (PATHS.CONNECTED_BUSY if not busy else PATHS.CONNECTED_FREE, self.hostname)

			try:
				self.zk.create(connection_path, value=self.worker_path.encode(), ephemeral=True)
				self.zk.set("%s/connection" % self.worker_path, value=connection_path.encode())
			except:
				pass

			try:
				self.zk.delete(delete_path)
			except:
				pass

			try:
				self.zk.delete("%s/%s" % (PATHS.DISCONNECTED, self.hostname), recursive=True)
			except:
				pass

			self.connection = connection_path
			self.busy = busy

		return self.connection

	def watch_new_exp(self):
		logging.debug('#Here5')
		kazoo.recipe.watchers.ChildrenWatch(self.zk, "%s/torun" % self.worker_path, self.exp_handler)

	def exp_get(self, exp_path):
		logging.debug('#Here6')
		exp_name, _ = self.zk.get(exp_path.decode('utf-8'))

		exp_cfg = WorkerClient.load_config_file("experiments/%s/info.cfg" % exp_name.decode('utf-8'))

		return Experiment(exp_path, exp_name, exp_cfg["parameters"], exp_cfg["actor_id"], eval(exp_cfg["is_snapshot"]))

	def exp_ready(self, exp_obj):
		logging.debug('#Here7')
		wc = WorkerClient(self.zk_addr)

		@self.zk.DataWatch('%s/start' % exp_obj.path)
		def ready(data, stat):
			if stat:
				exp_obj.run(wc)
				return False

	def exp_finished(self, exp_obj):
		logging.debug('Here8')
		#self.printd("exp finished")

		filename = "experiments/%s/%s." % (exp_obj.name, exp_obj.name)
		code_output = exp_obj.popen.poll() if not exp_obj.is_snapshot else exp_obj.snapshot.poll
		output = '(%i): ' % code_output
		try:
			f_output = open(filename + 'out', 'r+')
			f_error = open(filename + 'err', 'r+')
			error = f_error.read()

			output += '%s' % f_output.read()
			if error != '':
				output += '\nerror: ' + error
		except:
			output += 'Unable to run experiment'

		try:
			self.zk.create("%s/actors/%s/output" % (exp_obj.path, exp_obj.actor_id), value=output.encode())

			self.zk.delete("%s/torun/%s" % (self.worker_path, exp_obj.worker_torun_id), recursive=True)
		except:
			pass

		self.current_experiments.remove(exp_obj)

	def exp_handler(self, exp_diff):
		logging.debug('#Here8')
		logging.debug('[1]#torun')
		try:
			logging.debug('[2]#torun')
			exp_new = [n for n in exp_diff if n not in self.current_experiments]
			logging.debug('[3]#torun')
			for exp_id in exp_new:
				logging.debug('[4]#torun')
				if self.zk.exists("%s/torun/%s" % (self.worker_path, exp_id)):
					logging.debug('[5]#torun')
					# not deleted
					exp_path, _ = self.zk.get("%s/torun/%s" % (self.worker_path, exp_id))
					logging.debug('[6]#torun')
					exp_obj = self.exp_get(exp_path)
					logging.debug('[7]#torun')
					exp_obj.worker_torun_id = exp_id
					logging.debug('[8]#torun')
					#print "append... len current_experiments before %s"%len(self.current_experiments)
					self.current_experiments.append(exp_obj)
					logging.debug('[9]#torun')
					#print "append... len current_experiments before %s" % len(self.current_experiments)
					self.exp_ready(exp_obj)
					logging.debug('[10]#torun')
		except:
			logging.debug('[11]#torun')
			traceback.print_exc()
			logging.debug('[12]#torun')

	def exp_load(self):
		logging.debug('#Here9')
		logging.debug('[1]#exp_load')
		self.current_experiments = []  # Experiment objects
		logging.debug('[2]#exp_load')
		self.watch_new_exp()
		logging.debug('[3]#exp_load')

	def snap_get(self, actor_path):
		logging.debug('#Here10')
		if self.zk.exists("%s/data" % actor_path):
			s, _ = self.zk.get("%s/data" % actor_path)
			return eval(s)

		return None

	def snap_set(self, actor_path, value):
		logging.debug('#Here11')
		if self.zk.exists("%s/data" % actor_path):
			self.zk.set("%s/data" % actor_path, str(value).encode())
		else:
			self.zk.create("%s/data" % actor_path, str(value).encode())
