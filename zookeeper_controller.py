import logging
import subprocess
import sys
import os
import netifaces
import json
import time
import kazoo

from modules.conlib.controller_client import ControllerClient
from modules.conlib.remote_access import Channel
from time import sleep
from kazoo.client import *

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
MAX_ATTEMPTS = 180
DEFAULT_FILE_CONFIG = 'config.json'
data = json.load(open(DEFAULT_FILE_CONFIG))

def get_source():

    server_zk = ''

    for i in data['controllers']:

        server_zk+=i['remote_hostname']+':'+i['ClientPort']

    logging.info("get_source zk_addr: {}".format(server_zk))
    zk = KazooClient(server_zk, connection_retry=kazoo.retry.KazooRetry(max_tries=-1, max_delay=250))
    logging.info("zk: {}".format(zk))
    zk.add_listener(lambda x: os._exit(1) if x == KazooState.LOST else None)
    zk.start()
    file_name = "busyactor.txt"
    subprocess.call(["rm", "-f", file_name])
    fout = open(file_name, 'w+')
    busy_actor = None
    count_attempts = 0

    while busy_actor is None and count_attempts < MAX_ATTEMPTS:

        count_attempts += 1
        print("busy_actor: {} count_attempts: {}".format(busy_actor, count_attempts))
        
        for actor in zk.get_children('/connected/busy_workers'):
        
            print("found_actor!: {}".format(actor))
            fout.write("{}".format(actor))
            fout.close()
            sys.exit(0)
        
        sleep(1)

def nowStr():

    return time.strftime(TIME_FORMAT, time.localtime())


def get_tabs(n):
    
    s = ""
    
    for i in range(n):
    
        s += "\t"
    
    return s


def get_diff_tabs(n, word):

    s = ""

    for i in range(50 - len(word)):
        s += " "

    return s

DEFAULT_ZOOKEEPER_PATH = "/opt/zookeeper/bin"
class ZookeeperController:

    DEFAULT_ZOOKEEPER_PATH = "/opt/zookeeper/bin"
    DEFAULT_CONFIG_FILE = "config.json"
    DEFAULT_CONFIG_DATA = '''tickTime=5000\n\
    minSessionTimeout=30000\n\
    maxSessionTimeout=60000\n\
    initLimit=10\n\
    syncLimit=5\n\
    dataDir=~/.zk/datadir\n\
    clientPort=2181\n\
    clientPortAddress=NEW_IP\n\
    maxClientCnxns=200\n\
    '''
    ZK_CMD = ['{}/zkServer.sh'.format(DEFAULT_ZOOKEEPER_PATH)]

    def __init__(self, config_file_=DEFAULT_CONFIG_FILE, ensemble=False, ip_address='0.0.0.0', ip_list = None):

        logging.info("looking for zookeeper config file: {}".format(config_file_))

        if os.path.isfile(config_file_):

            logging.info("Config file found! {}".format(config_file_))
            self.config_data = json.load(open(config_file_))
            self.adapter = self.config_data["zookeeper_adapter"]

        else:

            logging.info("Config file not found! Config file name: '%s'" % config_file_)
            logging.info("You may want to create a config file from the available example: cp %s.example %s" % (
            ZookeeperController.DEFAULT_CONFIG_FILE, config_file_))
            sys.exit(-1)

        if not ensemble:

            self.zookeeper_ip_port = self.get_ip_adapter() + ':2181'
            logging.info("zookeeper_ip_port: {}".format(self.zookeeper_ip_port))
            self.create_zookeeper_config_file()

            if not self.is_running():

                logging.info("Zookeeper Service is not running.")
                self.start_zookeeper_service()

                if not os.path.isdir("./experiments"):

                    logging.info("CREATING EXPERIMENTS FOLDER")
                    os.mkdir("./experiments")

        else:
	
            if ip_list!= None:
            
            	self.zookeeper_ip_port = ip_list
            	logging.info("zookeeper_ip_port: {}".format(self.zookeeper_ip_port))
            	
            	if not self.is_running():
            	
            		logging.info("Zookeeper Service is not running.")
            		self.start_zookeeper_service()
            		
            		if not os.path.isdir("./experiments"):
            		
                    		logging.info("CREATING EXPERIMENTS FOLDER")
                    		
                    		os.mkdir("./experiments")
            
            	self.controller_client = None
            	return

            self.zookeeper_ip_port = ip_address+':2181'
            logging.info("zookeeper_ip_port: {}".format(self.zookeeper_ip_port))
            
            if not self.is_running():

                logging.info("Zookeeper Service is not running.")
                self.start_zookeeper_service()

                if not os.path.isdir("./experiments"):
                
                    logging.info("CREATING EXPERIMENTS FOLDER")
                    os.mkdir("./experiments")

        self.controller_client = None

    def set_controller_client(self, controller_client=None,ip_port='0.0.0.0'):

        if controller_client is None and self.controller_client is None:

            self.controller_client = ControllerClient(self.zookeeper_ip_port)
            self.controller_client.config_create_missing_paths()

        elif controller_client is not None:
            self.controller_client = controller_client

    def get_ip_adapter(self):

        netifaces.ifaddresses(self.adapter)
        return netifaces.ifaddresses(self.adapter)[netifaces.AF_INET][0]['addr']

    def create_zookeeper_config_file(self):

        new_my_config_file = ZookeeperController.DEFAULT_CONFIG_DATA.replace('NEW_IP', self.get_ip_adapter())
        zookeeper_config_file = "%s/conf/zoo.cfg"%ZookeeperController.DEFAULT_ZOOKEEPER_PATH
        text_file = open(zookeeper_config_file, "w")
        text_file.write(new_my_config_file)
        text_file.close()

    @staticmethod
    def get_status():

        cmd = 'sudo apache-zookeeper-3.6.1/bin/./zkServer.sh status'
        return os.popen(cmd).read()

    @staticmethod
    def is_running():

        a = os.popen('ps aux').read()
        
        if a.find('zookeeper')!=-1:

        	return True

        else:

        	return False


    @staticmethod
    def am_i_the_leader():

        cmd = ZookeeperController.DEFAULT_ZOOKEEPER_PATH+'/zkServer.sh status'
        status = os.popen(cmd).read()
        
        try:

            if status.index('leader'):

                return True

            else:

                return False

        except:

            return False

    @staticmethod
    def start_zookeeper_service():

        logging.info("STARTING ZK")
        cmd = ".{}/zkServer.sh start".format(DEFAULT_ZOOKEEPER_PATH)        
        subprocess.call(cmd, shell=True)

    @staticmethod
    def stop_zookeeper_service():

        logging.info("STOPPING ZK")
        cmd = ".{}/zkServer.sh  stop".format(DEFAULT_ZOOKEEPER_PATH)
        subprocess.call(cmd, shell=True)

    def reset_tasks(self):

        logging.info("\tRemoving tasks... ")

        for t in self.controller_client.zk.get_children('/tasks/'):

            logging.info("\t\ttask: {}".format(t))
            self.controller_client.zk.delete('/tasks/' + t, recursive=True)

        logging.info("\tRemoving tasks done. \n")
        logging.info("\tRemoving experiments from workers... ")

        try:

            for w in self.controller_client.zk.get_children('/registered/workers'):

                print(nowStr(), "\t\tRemoving experiment from worker: ", w)

                for e in self.controller_client.zk.get_children('/registered/workers/' + w + '/torun'):

                    print(nowStr(), "\t\t\tworker: ", w, " children: ", e)
                    self.controller_client.zk.delete('/registered/workers/' + w + '/torun/' + e, recursive=True)

        except Exception as e:

            logging.error("Excepetion: {}".format(e))

        logging.info("\tRemoving experiments from workers done.\n")

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

    def kill_actor_daemon(self, actor):

        print(nowStr(), "\tKilling an actor daemon process... ")

        try:

            logging.info("\t\tCreating channel with hostname: {} ".format(actor.hostname))
            channel = Channel(hostname=actor.hostname,
                              username=actor.username,
                              password=actor.password,
                              timeout=30)

            logging.info("\t\tStopping actor daemon process at worker: {}".format(actor.hostname))
            path = actor.get_remote_path()
            logging.info("\t\tChanging dir to: {}".format(path))
            channel.chdir(path)
            cmd = actor.get_command_stop()
            logging.info("\t\trunning command: {}".format(cmd))
            channel.run(cmd)

        except Exception as e:

            logging.error("\t\tException while stopping actor daemon: {} Exception: {}".format(actor.hostname, e))


    def print_zk_tree(self, tree_node, node, n, count_=1):

        if node is not None:

            print("%02d:%02d" % (n, count_), get_tabs(n), node, get_diff_tabs(n, node), " : ", end=' ')

            try:
            	

                value = self.controller_client.zk.get(tree_node)

                if value is None:
                    pass

                elif node == "pkey":

                    print(" RSA PRIVATE KEY ")

                else:

                    print(value[0])

            except Exception as e:

                print("Exception: ", e)

            try:

                count = 1
                for t in self.controller_client.zk.get_children(tree_node, include_data=False):
                    self.print_zk_tree(tree_node + "/" + t, t, n + 1, count)
                    count += 1

            except Exception as e:

                print("Exception: ", e)

if __name__ == '__main__':
    get_source()
