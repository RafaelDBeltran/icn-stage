import datetime, getopt, math, subprocess


from kazoo.client import KazooClient
from datetime import timedelta
import sys, os
# sys.path.append(os.getcwd() + '/..')
# from .. import modules

from modules.conlib.remote_access import Channel
from modules.conlib.controller_client import *
from modules.model.experiment import Experiment
from modules.model.role import Role
from modules.model.worker import Worker


import sys, time, logging, os, subprocess

import paramiko.rsakey, io

logging.basicConfig()

TIME_FORMAT = "%Y-%m-%d_%H-%M-%S"
EXPERIMENT_FILE_NAME = 'trackerlens.tar.gz'
WORKER_LIB_FILE_NAME = "worklib.tar.gz"

NUMBER_WORKERS_MONITORS = 15
NUMBER_WORKERS_SENTINELS = 5

NUMBER_WORKERS_MONITORS_2 = 15
NUMBER_WORKERS_SENTINELS_2 = 5


FILE_SERVER_ADDRESS = "acdc.inf.ufrgs.br"
FILE_SERVER_PORT = "80"
STATUS_SERVER_ADDRESS = "noc.inf.ufrgs.br"
STATUS_SERVER_PORT = "8080"

magnets_file_name = "magnet_torrent_list.txt"
plnodes_file_name = "pl_servers_teste.txt"
#plnodes_file_name = "pl_servers_all.txt"
start_time_str = ""
start_time_str2 = ""
role_sentinel = False



user = 'rnp_uuos'
pw = 'rnp_uuos_00'
pkey = '-----BEGIN RSA PRIVATE KEY-----\n\
Proc-Type: 4,ENCRYPTED\n\
DEK-Info: AES-128-CBC,728A21A91ADEFC6F87DD1C4BE7CFEA0B\n\
\n\
LtPH5k06V1DUsAs79SCClcOqQXtS8/mKgyKsapSnMTXBthtoZvIDvhpdKyX58THt\n\
Ed1pnhyWKmKTUuNcek7Kq+dATkQre3TtUo+o83eDug3Xgb93u9g/q115uq5CQL2N\n\
oNZKNcUapLBRrAPYBsLS64T7WGkkibDTkHUfh7p9/VCYdEPzKCYjrF72fEbM05j5\n\
+MvDlOx7kjt/WxdMUoB2Ht8OqO3G6TGHKBo1Rz9KMRnNqfrlpLnuAyx7CNbWC1ZS\n\
ROu0+oPVxIqKfa/zEz4hZRtLTt3LDxWwgYnfnYlKzXdf7d8UbRrm+m6eufWW9wKh\n\
s35gHb0AG3g0+PFBKeTpBrip1iLzVb4EvrG4yCrGy7MggpJkaok0EbYkPpwttmmy\n\
7m7DQ46Qt8HDqdVwwqNSkV87cfcwts+hiITgOJjAbbIOI4QKTmhzBqw3gLJpx1c/\n\
hThFOt0UfPaW7Fkl8y9dGcYd0wApdA2L77zWcVaVyNF3bkCdGpKDyG2WFZy8NF8s\n\
7aBdhvFHE3hxl3mDTSWWxw6NQmha/9shzfYqNyRkr5XBXLwayWJ1w9JJLQkxhqmO\n\
IRBfd0qNUToUyWMf/U0CCT+np6FmuhlmkSQxNGFKvJtM78fV9kA0xy8IlO44j4/J\n\
m6EcuPSfhg1ednKwy23S4he9yImmko8T+EwA6LMZOTYn8lMPXRTIwZy/AWQvPJbd\n\
sUd+1RNXrKY30NqlhHtMM5dQZ9eZC9YG3u5hMuxlG8R1MDnwKP1aQzhY2W7qf9/Q\n\
0hzrHXZf690eagPCzPsU32oBooxJltPGABTbEE+L9chxCzDe2SvgciYzuiP3aWNq\n\
SJBEjZE0zUoq9La70nEStlYP3O5tG4F6R3IeYT1V0FW6MlnhyurZ3SrnFDmS2hnj\n\
NeVg7rQD4lrr6LmWwPpLwTTKxs2TG3MF07VDIN2CrKHUp+VaMgQHeijgY0lPnh7X\n\
47oCWlVIKhl7FD57ef+NX6kImNkP40uExcWHjwCQeasfPAVUWBRkFSsnBF0fru+P\n\
/awr1IIkyj85u629+EU9tQgH8ty4/iiMUo3XWP3j8KD/GRIO3rRMOoHQ14/0Gsc7\n\
Tyncm8PU+h9Fc41znFBIeJScYtngmP4kR1X9Nc995PcbMRo5dErHjaxt9Kt/NTX7\n\
+Ip4OsQeaklAmerOJalpIiQXLfXk4Qu0l9oxVew14/guAsHaH7OXwX8JwPGXxhMg\n\
BkEwv/Sx2QfYy4Oxqyc3mmjym+G0hAtuhPLFINdAIGa9ERThnYdUiSJRMQl00Tfm\n\
a0bVKwAVwwCSsTYKZCSQKWM7LAEO5ucmgTb2ZDRQrakb48u0XRVuk0QizuzZDar4\n\
4VnWhMfMu2wApYatW9mdY7F5ExgLYxheHql9pGClNflQrqR9KxtmYi6QHP4lmCLn\n\
gn4N7FdVFvf+0QSFHTy5M1yKUB72sYAMBccVcj9RZLjyCvlmVA4a6SSFgFgS5ueo\n\
6ODDuQY1D5XW9NGb9g/l9vblG1QH0CIadiDPGV0ltVHMfnDN8axLD/CKWB+VL+Fu\n\
8SiTXbBmy/IHFPuzzz5x39e7t7DQQ4CovlnMBBl0nTSnwO3EKQlkNjcsrBGMoVhV\n\
-----END RSA PRIVATE KEY-----'



pkey_am = '-----BEGIN RSA PRIVATE KEY-----\n\
Proc-Type: 4,ENCRYPTED\n\
DEK-Info: AES-128-CBC,932187F127FD6F1523CC3E942F51671C\n\
\n\
Xm2g+PxL7gqQLMZrFq+rReRxYVDJqKKPHyyfW7KYaxjwhFfdn/bw4sepf+Ekm6No\n\
NvJIvwibAkxCZuowdG05jVNXwmGw1E9sx0EsasmMAxfEUHNE+kLAOy1A8c60JAFv\n\
cqT0Bzx7DtQYj4yLlRbSUA/mj2AfCBMXVYmyWLoGzpl7bOy1ZgsdTUzn6pZz88RH\n\
F0WNLcAwqw5IZGWqWL+9/X/gZd7DIAS9+UVBFHw86yWuIDziSloNcs4Q6mCbEyok\n\
S7h/iTuFNeQt1iMGicP0XQlN/++CII/jJ9ci7GF8t90io0n3UqQiPs6sxlw2/Tf/\n\
W9oGDmNYic7H78JoL2sX+z9kLY+4WtAazpkqWRpMqSXUjX2R9WjIMr1D4uS9+qo2\n\
8PI7ed9q7VWYlFMpzO/TG0AXEZKzfXp1BQdcO/tpZ6P6Yh+hotmsM9MSFN38lAtB\n\
B/bBKVJeaw57N0v8XTpYDpnY8w7KAwy7K6t2+wv3Y5QwYSmjDWKAepBujZ4ACbJH\n\
YwETxRhOgTX9pIxPj5mtymlOBlCWrG4hCq/P7IyqXvF9UTkjj+FGqI4cBG33oLX4\n\
Uz8vFG0Mx1NmSuFOdzTPfvsK2UJVdPHn+VHYrYNcNybvgMS7o+t1T+d5sAdYDuEL\n\
okZYX4+iM7Ez026TDBhjBXM06t3zedlN3ktbZGAjlyO4AE8QA77QsTIak/0FNMhy\n\
FCR+jhnwVH9VhnjsgZu0V1shwF2MH5LE0sLa3Mr7hBTghtn9jmcJ8uSWUQKdu5c+\n\
pJpP1snvoSEUVdHWw4U/1SzHEg3JD121hadxNRFYRgjy9ltmBwbrbcGdoqAef4zC\n\
26l/ShxmZLylAwwfplnieI2diTe30Yb9zIMDBtxWORd1Tr6BtBZekQK8qnpqYX+L\n\
h5v/lJ5778aIS2MQiDal3xrba7D9igBnPRjR+YpJ+1FXmIUyy3jTp1SoSCrzaZy5\n\
hQii555QTQ9IzPJ1mb5UciETqROITvlFN3MWjGv6yMQvTWiotZ9wPTHrsjOsudQs\n\
isw/cnAOK5a6TfhYA+KSSTF1HEFiE0baB5vprP80bFZLOtAGCITocKvPXt+xfeGy\n\
WjZhtzxi4ZBi/JMZDzhSftVGI/IYSds4atWqvUGKRWVFK86b/AGfKg4qXdM/17PS\n\
17MfNjN/KFswCSiOd5LhM0tHW+eHyBE1bFvT6MpHgm5WIMz7yVE+QR0oVsl/09FC\n\
PnrOsWuF4wf2Y6icxvvImmNmWNGn7AkksutVJhI1+ILAmBMd4xunN7xq78eg5Nva\n\
itLpOuuzJtCq7UyIbX5EVlGEY08r8kmRI3M52TLd+auDKT649yJBPheVV9Go77Z9\n\
42x9/qHxSSPPqrtierb+AyMW8x3m0Ph5B1CAsEiE5+Yf3Oprvrvd3rcpZPoj3stw\n\
lju7YNwDOHz1RU8Cl+6mAxzkwic4TP8MQ0cvAUtuSfVJ1Sivnex6RkTomWGyuxt6\n\
uNVnOfi8Altt/YST4x7NdkQ8Nmgz3bfaWXhbsJsLumvO2U9zYDj7zEoszvPF2qDu\n\
09fGJeUNTHuwxrVoGM3sNW0JAofla5P2FkO3TRrZZ0wZynxqiMpYjw25b7ub7fkQ\n\
-----END RSA PRIVATE KEY-----'


def nowStr():
	return time.strftime(TIME_FORMAT, time.localtime())

# STATUS SERVER'S METHODS


def start_status_server(status_server_port, experiment_name):
	cmd = "python status_server_trackerlens.py restart --port %s --name %s" % (status_server_port, experiment_name)
	print("starting status server (%s) " % cmd)
	param = cmd.split(" ")
	subprocess.Popen(param, cwd=os.getcwd())
	print("waint 10 seconds... ", end=' ')
	time.sleep(10)
	print("done.")#client_address


def stop_status_server():
	cmd = "python status_server_trackerlens.py stop "
	param = cmd.split(" ")
	print("Stopping status server (%s)"%cmd)
	popen = subprocess.Popen(param, cwd=os.getcwd())
	popen.wait()


def get_tabs(n):
	s = ""
	for i in range(n):
		s += "\t"
	return s

def get_diff_tabs(n, word):
	s = ""
	for i in range(50-len(word)):
		s += " "

	#for i in range(8-n):
	#	s += "\t"
	return s


def print_zk_tree(tree_node, node, n, count_=1):

	if node is not None:

		print("%02d:%02d"%(n,count_), get_tabs(n), node, get_diff_tabs(n, node), " : ", end=' ')
		try:
			value = cclient.zk.get(tree_node)
			if value is None:
				print("")
			else:
				print(value[0])

		except Exception as e:
			print("Exception: ", e)


		try:
			count = 1
			for t in cclient.zk.get_children(tree_node, include_data=False):
				print_zk_tree(tree_node+"/"+t, t, n+1, count)
				count +=1
				#print t
		except Exception as e:
			print("Exception: ", e)


def download_files_from_workers(remote_path_, local_path_, window_begin_, window_end_):
	print(nowStr(), "Downloading files from workers")
	print(nowStr(), "local_path:%s" % local_path_)
	print(nowStr(), "remote_path:%s" % remote_path_)
	#workers = cclient.zk.get_children('/registered/workers')
	workers = ["planetlab2.koganei.itrc.net"]
	for w in workers:
		try:
			#commands.getoutput("mkdir %s/%s" % local_path)

			print(nowStr(), "\t\tCreating channel with worker: ", w, " ... ", end=' ')
			channel = Channel(hostname=w, username=user, password=pw, pkey=pkey, timeout=30)
			print(" done.")

			print(nowStr(), "\t\tChanging dir to ", remote_path_, " ... ", end=' ')
			channel.chdir(remote_path_)
			print(" done.")

			count = window_begin_
			#-1  Force output to be one entry per line.
			stdout, stderr = channel.run("ls -1 *.gz")
			stdout_str = stdout.read().strip()
			for file_name in stdout_str.split("\n"):
				file_id = "r%04d.gz"% count
				if file_id in file_name:

					#print "----"
					#print remote_file_name
					#print "----"
					print(nowStr(), "\t\t\tCount:%d end:%d file_id:%s file_name:%s ... " % (count, window_end_, file_id, file_name), end=' ')
					get_done = channel.get(file_name, local_path_)
					print(" done: ", end=' ')
					if get_done:
						print("SUCCESS!")
					else:
						print("FAILED.")
						sys.exit(-1)
					count += 1

				if count > window_end_:
					break

		except Exception as e:
			print("\n\n")
			print(" error while downloading file from worker ")
			raise e


def reset_workers():
	print(nowStr(), "Reseting workers...\n")

	print(nowStr(), "\tRemoving tasks... ")
	for t in cclient.zk.get_children('/tasks/'):
		print(nowStr(), "\t\ttask: ", t)
		cclient.zk.delete('/tasks/' + t, recursive=True)
	print(nowStr(), "\tRemoving tasks done. \n")

	print(nowStr(), "\tKilling all worker daemon (python) process... ")
	for w in cclient.zk.get_children('/registered/workers'):
		try:
			print(nowStr(), "\t\tCreating channel with worker: ", w, " ... ", end=' ')
			channel = Channel(hostname=w, username=user, password=pw, pkey=pkey, timeout=30)
			print(" done.")
			print(nowStr(), "\t\tKilling python process at worker: ", w, " ... ", end=' ')
			channel.run("killall python")
			print(" done.")
		except Exception as e:
			print("\n\n")
			print(" error while killing worker ", w)
			print(e)

	print(nowStr(), "\tKilling done. \n")

	print(nowStr(), "\tRemoving experiments from workers... ")
	try:
		for w in cclient.zk.get_children('/registered/workers'):
			print(nowStr(), "\t\tRemoving experiment from worker: ", w)
			for e in cclient.zk.get_children('/registered/workers/' + w + '/torun'):
				print(nowStr(), "\t\t\tworker: ", w, " children: ", e)
				cclient.zk.delete('/registered/workers/' + w + '/torun/' + e, recursive=True)
	except:
		pass
	print(nowStr(), "\tRemoving experiments from workers done.\n")

	print(nowStr(), "\tRemoving registered workers... ")
	for w in cclient.zk.get_children('/registered/workers'):
		print(nowStr(), "\t\tregistered worker: ", w)
		cclient.zk.delete('/registered/workers/' + w, recursive=True)
	print(nowStr(), "\tRemoving registered workers done.\n")

	print(nowStr(), "\tRemoving connected busy workers... ")
	for w in cclient.zk.get_children('/connected/busy_workers'):
		print(nowStr(), "\t\tconnected busy worker: ", w)
		cclient.zk.delete('/connected/busy_workers/' + w, recursive=True)
	print(nowStr(), "\tRemoving connected busy workers done.\n")

	print(nowStr(), "\tRemoving connected free workers... ")
	for w in cclient.zk.get_children('/connected/free_workers/'):
		print(nowStr(), "\t\tconnected free worker: ", w)
		cclient.zk.delete('/connected/free_workers/' + w, recursive=True)
	print(nowStr(), "\tRemoving connected free workers done.\n")

	print(nowStr(), "\tRemoving disconnected workers... ")
	for w in cclient.zk.get_children('/disconnected/workers/'):
		print(nowStr(), "\t\tdisconnected worker: ", w)
		cclient.zk.delete('/disconnected/workers/' + w, recursive=True)
	print(nowStr(), "\tRemoving disconnected workers done.\n")

	print(nowStr(), "\tRemoving experiments... ")
	for e in cclient.zk.get_children('/experiments/'):
		print(nowStr(), "\t\t experiment: ", e)
		cclient.zk.delete('/experiments/' + e, recursive=True)
	print(nowStr(), "\tRemoving experiments done.\n")

	print(nowStr(), "Removing done. \n")


def add_workers():
	# restart workers
	print(nowStr(), "Adding workers... ")
	for h in hosts:
		print(nowStr(), "\tadding task NEW_WORKER: %s" % h)
		#cclient.task_add(COMMANDS.NEW_WORKER, worker=Worker(h, user, password=pw, pkey=pkey))
		cclient.task_add(COMMANDS.NEW_WORKER, worker=Worker(h, "user", password="password", pkey="pkey"))

	print(nowStr(), "Adding done.\n")


# EXPERIMENT'S METHODS

def reconnect_disconnected_workers():

	#stop_status_server()
	print(nowStr(), "\tReconnecting (and updating) disconnected workers... ")
	for w in cclient.zk.get_children('/disconnected/workers'):
		print(nowStr(), "\t\tDisconnected worker: ", w)
		#cclient.task_add(COMMANDS.START_WORKER, worker=Worker(w, "user", password="password", pkey="pkey"))

		try:
			print(nowStr(), "\t\t\tCreating channel with worker: ", w, " ... ", end=' ')
			channel = Channel(hostname=w, username=user, password=pw, pkey=pkey, timeout=30)
			print(" done.")

			print(nowStr(), "\t\t\tsending %s to worker: "%WORKER_LIB_FILE_NAME, w, " ... ", end=' ')\

			channel.put(WORKER_LIB_FILE_NAME, WORKER_LIB_FILE_NAME)
			channel.run("tar -xzf %s" %WORKER_LIB_FILE_NAME)
			print("done.")

			channel.chdir("~/worker/")
			cmd = "python daemon_worker.py restart "
			print(nowStr(), "\t\t\trunning cmd: cd ~/worker/; %s ..."%cmd, end=' ')
			stdout, stderr = channel.run(cmd)
			stderr_str = stderr.read().strip()
			stdout_str = stdout.read().strip()

			print(" stdout:%s stderr:%s done."%(stdout_str, stderr_str))

		except Exception as e:
			print(" exception: ", e)
			#print nowStr(),"\t\t\tan exception occurred while restarting the worker ", w, " exception: ", e

	print(nowStr(), "\tReconnecting disconnected workers done.\n")


# ping noc.inf.ufrgs.br -c 1

def ping_noc_on_connected_workers(debug_=False):
	print(nowStr(), "\tPing noc.inf.ufrgs.br on all (busy or free) connected workers... ")
	connected_workers = cclient.zk.get_children('/connected/busy_workers')
	connected_workers += cclient.zk.get_children('/connected/free_workers')
	number_connected_workers = len(connected_workers)
	i_connected_workers = 0
	for w in connected_workers:
		if debug_:
			print(nowStr(), "\t\tConnected worker (%02d/%d): %s"%(i_connected_workers, number_connected_workers, w))
		i_connected_workers += 1
		# cclient.zk.delete('/connected/busy_workers/' + w, recursive=True)
		try:
			if debug_:
				print(nowStr(), "\t\t\tCreating channel with worker: ", w, " ... ", end=' ')
			channel = Channel(hostname=w, username=user, password=pw, pkey=pkey, timeout=30)
			if debug_:
				print(" done.")

			cmd = "ping noc.inf.ufrgs.br -c 1 "
			if debug_:
				print(nowStr(), "\t\t\t running cmd: %s " % cmd)
			stdout, stderr = channel.run(cmd)
			ls_result_err = stderr.read().strip()
			ls_result_out = stdout.read().strip()

			# print nowStr(), "\t\t\tstderr: %s " % ls_result_err
			# print nowStr(), "\t\t\tstdout: %s " % ls_result_out
			if len(ls_result_err) > 0 :
				print(nowStr(), "\t\t\t [FAILED] (%02d/%d)"%(i_connected_workers, number_connected_workers), w, " stderr: %s "%ls_result_err)

			if len(ls_result_out) > 0:
				if not debug_:
					ls_result_out = ls_result_out.split("\n")[0]

				print(nowStr(), "\t\t\t [OK]     (%02d/%d)"%(i_connected_workers, number_connected_workers), w, " stdout: %s "%ls_result_out)

		except Exception as e:
			print(nowStr(), "\t\t\t [FAILED] (%02d/%d)"%(i_connected_workers, number_connected_workers), w, " exception: ", e)
			#print "\n\n"
			#print " Exception while ping back  worker :", w, " Exception: ", e
			#raise e

	print(nowStr(), "\tTesting ping back on all connected workers done.\n")


def stop_current_monitoring_at_busy_workers():

	#stop_status_server()
	print(nowStr(), "\tStoping monitoring at all connected busy workers... ")
	for w in cclient.zk.get_children('/connected/busy_workers'):
		print(nowStr(), "\t\tConnected busy worker: ", w)
		#cclient.zk.delete('/connected/busy_workers/' + w, recursive=True)
		try:
			print(nowStr(), "\t\t\tCreating channel with worker: ", w, " ... ", end=' ')
			channel = Channel(hostname=w, username=user, password=pw, pkey=pkey, timeout=30)
			print(" done.")

			#print nowStr(), "\t\tStoping monitoring at worker: ", w, " ... ",
			experiment_script="trackerlensdaemon.py"
			cmd = "ls %s "%experiment_script
			print(nowStr(), "\t\t\tcmd: %s " % cmd)
			stdout, stderr = channel.run(cmd)
			ls_result_err = stderr.read().strip()
			ls_result_out = stdout.read().strip()

			#print nowStr(), "\t\t\tstderr: %s " % ls_result_err
			#print nowStr(), "\t\t\tstdout: %s " % ls_result_out
			if ls_result_out != experiment_script:
				print(nowStr(), "\t\t\tfile NOT found: %s "%experiment_script)
				print(nowStr(), "\t\t\tuploading file: %s " % EXPERIMENT_FILE_NAME, end=' ')
				channel.put("experiments/" + EXPERIMENT_FILE_NAME, EXPERIMENT_FILE_NAME)
				print("done.")

				print(nowStr(), "\t\t\tunzipping file: %s " % EXPERIMENT_FILE_NAME, end=' ')
				channel.run("tar -xzf %s" %EXPERIMENT_FILE_NAME)
				print("done.")

			else:
				print(nowStr(), "\t\t\tfile found: %s "%experiment_script)

			cmd = "python %s stop"%experiment_script
			print(nowStr(), "\t\t\trunning cmd : %s ..."%cmd, end=' ')
			channel.run(cmd)
			print(" done.")

		except Exception as e:
			print("\n\n")
			print(" error while killing worker ", w)
			raise e

	print(nowStr(), "\tStoping task at busy workers done.\n")


def start_experiment():
	experiment_name = "rm_trlens_%s"%(start_time_str)
	#remove experiments
	print("\n\nExperiment: %s"%(experiment_name))
	print("----------------------------------------------------------------")

	stop_status_server()
	stop_current_monitoring_at_busy_workers()

	start_status_server(STATUS_SERVER_PORT, experiment_name)
	add_workers()
	number_workers = len(hosts) #NUMBER_WORKERS_MONITORS + NUMBER_WORKERS_MONITORS_2 + NUMBER_WORKERS_SENTINELS + NUMBER_WORKERS_SENTINELS_2
	setup_delay_sec = (10*number_workers)
	print(nowStr(), " Waiting %d seconds for setup %d workers... "%(setup_delay_sec, number_workers))
	time.sleep(setup_delay_sec)
	print(nowStr()," done.\n")

	#send experiment
	print(nowStr()," Adding experiment task... ", end=' ')

	#Actor parametes: '--sentinel', '--input=', '--time', '--fserver', '--fport', '--sserver', '--sport'
	parameters = "python trackerlensdaemon.py restart "
	parameters += " -i %s" % magnets_file_name
	parameters += " -s %s" % FILE_SERVER_ADDRESS
	parameters += " -p %s" % FILE_SERVER_PORT
	parameters += " -u %s" % STATUS_SERVER_ADDRESS
	parameters += " -q %s" % STATUS_SERVER_PORT

	role_monitor = Role('monitor1', "%s -t %s"%(parameters, start_time_str), NUMBER_WORKERS_MONITORS)
	roles = [role_monitor]

	if NUMBER_WORKERS_SENTINELS>0:
		role_sentinel = Role('sentinel1', "%s -t %s --sentinel "%(parameters, start_time_str), NUMBER_WORKERS_SENTINELS)
		roles.append(role_sentinel)

	if NUMBER_WORKERS_MONITORS_2>0:
		role_monitor2 = Role('monitor2', "%s -t %s"%(parameters, start_time_str2), NUMBER_WORKERS_MONITORS_2)
		roles.append(role_monitor2)

	if NUMBER_WORKERS_SENTINELS_2>0:
		role_sentinel2 = Role('sentinel2', "%s -t %s --sentinel "%(parameters, start_time_str2), NUMBER_WORKERS_SENTINELS_2)
		roles.append(role_sentinel2)

	experiment = Experiment(name=experiment_name, filename=EXPERIMENT_FILE_NAME, roles=roles, is_snapshot=False)
	cclient.task_add(COMMANDS.NEW_EXPERIMENT, experiment=experiment)
	print(" done. ")

	#print nowStr(), " Running experiment. Waiting %d seconds (%d minutes)... "%(exp_duration_sec, exp_duration_min)

	# #wait
	# time.sleep(exp_duration_sec)
	# print nowStr(), " Experiment done."
    #
	# if not cclient.zk.connected:
	# 	print datetime.datetime.now()," Starting... cclient.zk.start()",
	# 	cclient.zk.start()
	# 	print "done."
	# else:
	# 	print nowStr(), " cclient.zk.connected "


def print_usage():
	print('''
	
	EasyExp - TrackerLens for Monitoring The BitTorrent Universe
	------------------------------------------------------------
	
	USAGE: %s COMMAND [OPTIONS]   
	
	The commands are as follows:
	help\t show this message
	ping\t (option debug) ping noc.inf.ufrgs.br on all connected (busy or free) servers. Useful to test remote DNS config.
	reconnect\t try to reconnect disconnected workers
	print\t zookeeper data tree (option: root node)
	printc\t shortcut to printing zookeeper data tree for the connected workers 
	printd\t shortcut to printing zookeeper data tree for the disconnected workers 
	stop\t monitoring 
	add\t worker daemons (using zookeeper)
	#disabled! reset\t worker daemons (kill processes using remote access and delete zookeeper nodes)
	start\t a monitoring
	
	The options are as follows:
	-t | --time    = global time to begin the monitoring in the format '%s' 
	-p | --plnodes = name of the file with planet lab nodes (default=%s)
	-m | --magnets = name of the file with magnet links of bittorrent swarms (default=%s)

'''%(__file__, TIME_FORMAT, plnodes_file_name, magnets_file_name))

#restart\t worker daemons (using zookeeper)

def check_file(file_name_):
	if os.path.isfile(file_name_):
		print("[OK] file found! " + file_name_)
	else:
		print("[ERROR] file not found! " + file_name_)
		sys.exit(-1)


if __name__ == '__main__':

	try:
		start_time_str = nowStr()
		dt1 = datetime.datetime.strptime(start_time_str, TIME_FORMAT)
		# print "dt1: ", dt1
		dt2 = dt1 + timedelta(minutes=130)
		start_time_str = datetime.datetime.strftime(dt2, TIME_FORMAT)
	except Exception as e:
		print(e)

	cclient = ControllerClient()

	if len(sys.argv) == 1 or sys.argv[1] in ['help', '--help', 'h', '-h', '--h']:
		print_usage()

	elif sys.argv[1] == 'reconnect':
		reconnect_disconnected_workers()
		cclient.zk.stop()
		sys.exit(0)

	elif sys.argv[1] == 'ping':
		debug = False
		if len(sys.argv) > 2:
			debug = True
		ping_noc_on_connected_workers(debug)
		cclient.zk.stop()
		sys.exit(0)

	elif sys.argv[1] == 'printc':
		try:
			root = "/connected/"
			print_zk_tree(root, root, 0)

		except:
			pass
		cclient.zk.stop()
		sys.exit(0)

	elif sys.argv[1] == 'printd':
		try:
			root = "/disconnected/"
			print_zk_tree(root, root, 0)

		except:
			pass
		cclient.zk.stop()
		sys.exit(0)

	elif sys.argv[1] == 'print':
		try:
			if len(sys.argv) > 2:
				root = sys.argv[2]
				#print root, "/" + root.split("/")[len(root.split("/")) - 1]
				print_zk_tree(root, root, 0)
			else:
				print_zk_tree("/", "/", 0)

		except:
			pass
		cclient.zk.stop()
		sys.exit(0)

	elif sys.argv[1] == 'stop':
		print("stopping the current monitoring...")
		stop_current_monitoring_at_busy_workers()

	elif sys.argv[1] == 'download':
		experiment = "rm_trlens_2018-11-30_17-00-00"
		remote_path = "/home/rnp_uuos/worker/experiments/" + experiment + "/"
		local_path = "/home/rmansilha/controller/" + experiment + "/"
		subprocess.getoutput("mkdir %s" % local_path)
		window_begin = 799
		window_end = 801
		print("downloadign files from experiment:%s begin:%d end:%d " % (experiment, window_begin, window_end))
		download_files_from_workers(remote_path, local_path, window_begin, window_end)

	else:

		#if sys.argv[1] == 'add':
		#	plnodes_file_name = "pl_servers_add.txt"

		try:
			optlist, args = getopt.gnu_getopt(sys.argv[2:], 't:p:m:', ['time=', 'plnodes=', 'magnets='])

			for o, a in optlist:
				print("option: '%s' \t\targument: '%s'" % (o, a))
				if o in ["-t", "--time"]:
					start_time_str = a
					try:
						time.strptime(start_time_str, TIME_FORMAT)

					except:
						print("Error: time '%s' isn't in the expect format '%s'" % (start_time_str, TIME_FORMAT))
						sys.exit(-1)

				elif o in ["-p", "--plnodes"]:
					plnodes_file_name = a

				elif o in ["-m", "--magnets"]:
					magnets_file_name = a

				else:
					print("error: option '%s' not recognized" % o)
					sys.exit(-1)

		except getopt.GetoptError as e:
			print("Error: ", e, "\n\n")
			print_usage()
			sys.exit(-1)

		try:
			dt1 = datetime.datetime.strptime(start_time_str, TIME_FORMAT)
			# print "dt1: ", dt1
			dt2 = dt1 + timedelta(minutes=15)
			start_time_str2 = datetime.datetime.strftime(dt2, TIME_FORMAT)
		except Exception as e:
			print(e)

		print("")
		print("Settings")
		print("--------")
		print(" experiment_file_pkg\t= " + EXPERIMENT_FILE_NAME)
		print(" magnets_file_name\t= " + magnets_file_name)
		print(" plnodes_file_name\t= " + plnodes_file_name)
		print(" start_time_str\t\t= " + start_time_str)
		print(" start_time_str2\t= " + start_time_str2)

		print("")
		print("Checking files")
		print("--------------")
		#check_file("experiments/" + EXPERIMENT_FILE_NAME)
		#check_file(magnets_file_name)
		#check_file(plnodes_file_name)

		#hosts = []
		#f = open(plnodes_file_name)
		#for line in f:
	#		if len(line.strip())>0 and not "#" == line[0]:
	#			hosts.append(line.strip())

		if sys.argv[1] == 'add':
			print("Command: ADD WORKERS")
			add_workers()

		elif sys.argv[1] == 'reset':
			print("Command: RESET WORKERS (and their monitoring)")
			#print "Command disabled!"
			reset_workers()

		elif sys.argv[1] == 'start':
			print("Command: START MONITORING")
			start_experiment()

		else:
			print("Command unrecognized: '%s'" % sys.argv[1])
			print_usage()
