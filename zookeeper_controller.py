import logging
import subprocess
import sys
import os

from modules.conlib.controller_client import *
from modules.conlib.remote_access import Channel

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'

def nowStr():
	return time.strftime(TIME_FORMAT, time.localtime())
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



class Zookeeper_Controller:
    def __init__(self):
        try:
            self.controller_client = ControllerClient()
        except:
            self.zookeeper_start()
        print('start zookeeper controller')

    def zookeeper_status(self):
        logging.info("STATUS ZK")
        subprocess.call("%s daemon_controller.py status" % sys.executable, shell=True)

    def zookeeper_restart(self):
        logging.info("RESTART ZK")
        subprocess.call("%s daemon_controller.py restart" % sys.executable, shell=True)

    def zookeeper_stop(self):
        logging.info("STOP ZK")
        subprocess.call("%s daemon_controller.py stop" % sys.executable, shell=True)

    def zookeeper_start(self):
        logging.info("STARTING ZK")
        # subprocess.call("./zookeeper-3.4.9/bin/zkServer.sh start", shell=True)
        subprocess.call("./apache-zookeeper-3.6.1/bin/zkServer.sh start", shell=True)
        
        logging.info("CONNECTING ZK")
        #controller_client = ControllerClient()
        self.controller_client = ControllerClient()

        logging.info("CREATING BASIC ZNODES ZK")
        self.controller_client.config_create_missing_paths()

        if not os.path.isdir("./experiments"):
            logging.info("CREATING EXPERIMENTS FOLDER")
            os.mkdir("./experiments")

        subprocess.call("%s daemon_controller.py restart" % sys.executable, shell=True)
    #TODO Há varias etapas redundantes, da pra reduzir pela metade esse metodo.
    def reset_workers(self):
        print(nowStr(), "Reseting workers...\n")

        print(nowStr(), "\tRemoving tasks... ")
        for t in self.controller_client.zk.get_children('/tasks/'):
            print(nowStr(), "\t\ttask: ", t)
            self.controller_client.zk.delete('/tasks/' + t, recursive=True)
        print(nowStr(), "\tRemoving tasks done. \n")

        print(nowStr(), "\tRemoving experiments from workers... ")
        try:
            for w in self.controller_client.zk.get_children('/registered/workers'):
                print(nowStr(), "\t\tRemoving experiment from worker: ", w)
                for e in self.controller_client.zk.get_children('/registered/workers/' + w + '/torun'):
                    print(nowStr(), "\t\t\tworker: ", w, " children: ", e)
                    self.controller_client.zk.delete('/registered/workers/' + w + '/torun/' + e, recursive=True)
        except:
            pass
        print(nowStr(), "\tRemoving experiments from workers done.\n")

        print(nowStr(), "\tRemoving registered workers... ")
        for w in self.controller_client.zk.get_children('/registered/workers'):
            print(nowStr(), "\t\tregistered worker: ", w)
            self.controller_client.zk.delete('/registered/workers/' + w, recursive=True)
        print(nowStr(), "\tRemoving registered workers done.\n")

        print(nowStr(), "\tRemoving connected busy workers... ")
        for w in self.controller_client.zk.get_children('/connected/busy_workers'):
            print(nowStr(), "\t\tconnected busy worker: ", w)
            self.controller_client.zk.delete('/connected/busy_workers/' + w, recursive=True)
        print(nowStr(), "\tRemoving connected busy workers done.\n")

        print(nowStr(), "\tRemoving connected free workers... ")
        for w in self.controller_client.zk.get_children('/connected/free_workers/'):
            print(nowStr(), "\t\tconnected free worker: ", w)
            self.controller_client.zk.delete('/connected/free_workers/' + w, recursive=True)
        print(nowStr(), "\tRemoving connected free workers done.\n")

        print(nowStr(), "\tRemoving disconnected workers... ")
        for w in self.controller_client.zk.get_children('/disconnected/workers/'):
            print(nowStr(), "\t\tdisconnected worker: ", w)
            self.controller_client.zk.delete('/disconnected/workers/' + w, recursive=True)
        print(nowStr(), "\tRemoving disconnected workers done.\n")

        print(nowStr(), "\tRemoving experiments... ")
        for e in self.controller_client.zk.get_children('/experiments/'):
            print(nowStr(), "\t\t experiment: ", e)
            self.controller_client.zk.delete('/experiments/' + e, recursive=True)
        print(nowStr(), "\tRemoving experiments done.\n")

        print(nowStr(), "Removing done. \n")

    def kill_worker_daemon(self, remote_user, remote_password, remote_pkey):
        print(nowStr(), "\tKilling all worker daemon (python) process... ")
        for w in self.controller_client.zk.get_children('/registered/workers'):
            try:
                print(nowStr(), "\t\tCreating channel with worker: ", w, " ... ", end=' ')
                channel = Channel(hostname=w, username=remote_user, password=remote_password, pkey=remote_pkey, timeout=30)
                print(" done.")
                print(nowStr(), "\t\tKilling python process at worker: ", w, " ... ", end=' ')
                channel.run("killall python")
                print(" done.")
            except Exception as e:
                print("\n\n")
                print(" error while killing worker ", w)
                print(e)

        print(nowStr(), "\tKilling done. \n")
    

    def print_zk_tree(self, tree_node, node, n, count_=1):

        if node is not None:

            print("%02d:%02d"%(n,count_), get_tabs(n), node, get_diff_tabs(n, node), " : ", end=' ')
            try:
                value = self.controller_client.zk.get(tree_node)
                if value is None:
                    print("")
                else:
                    print(value[0])

            except Exception as e:
                print("Exception: ", e)


            try:
                count = 1
                for t in self.controller_client.zk.get_children(tree_node, include_data=False):
                    self.print_zk_tree(tree_node+"/"+t, t, n+1, count)
                    count +=1
                    #print t
            except Exception as e:
                print("Exception: ", e)