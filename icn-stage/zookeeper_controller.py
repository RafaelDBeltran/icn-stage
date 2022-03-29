# -*- coding: iso-8859-15 -*-

import logging
import subprocess
import sys
import os
import netifaces
import json
import time
from modules.conlib.controller_client import ControllerClient
from modules.conlib.remote_access import Channel
from modules.util.tools import Sundry
from time import sleep
from kazoo.client import *
import kazoo

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
MAX_ATTEMPTS = 60*3

def get_source(zk_addr='10.0.2.15:2181'):

    logging.info("get_source zk_addr: {}".format(zk_addr))
    zk = KazooClient(zk_addr, connection_retry=kazoo.retry.KazooRetry(max_tries=-1, max_delay=250))
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

    # for i in range(8-n):
    #	s += "\t"
    return s


class ZookeeperController:
    DEFAULT_USER_PATH = "/icn"
    DEFAULT_ZOOKEEPER_PATH = DEFAULT_USER_PATH + "/opt/zookeeper"
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
    ZK_CMD = '{}/bin/zkServer.sh'.format(DEFAULT_ZOOKEEPER_PATH.replace("''", "'"))

    def __init__(self, config_file_=DEFAULT_CONFIG_FILE):
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
            # self.create_zookeeper_config_file()

        self.zookeeper_ip_port = self.get_ip_adapter() + ':2181'
        sundry_instance = Sundry()
        #self.zookeeper_ip_port = sundry_instance.get_ensemble_ips('settings.json')
        logging.info("zookeeper_ip_port: {}".format(self.zookeeper_ip_port))
        #self.create_zookeeper_config_file()

        if not self.is_running():
            logging.info("Zookeeper Service is not running.")
            self.start_zookeeper_service()
            #logging.info("CONNECTING ZK")
            #self.controller_client = None # ControllerClient(zookeeper_ip_port)

            #logging.info("CREATING BASIC ZNODES ZK")
            #self.controller_client.config_create_missing_paths()

            if not os.path.isdir("./experiments"):
                logging.info("CREATING EXPERIMENTS FOLDER")
                os.mkdir("./experiments")
        #else:
        #    self.controller_client = ControllerClient(zookeeper_ip_port)
        # instantiating it is costly and might not be need at all, so leave the decision for the caller
        self.controller_client = None

    def set_controller_client(self, controller_client=None):
        if controller_client is None and self.controller_client is None:
            self.controller_client = ControllerClient(self.zookeeper_ip_port)
        elif controller_client is not None:
            self.controller_client = controller_client

    def get_ip_adapter(self):
        # Como o ip do fibre eh dinamico, essa funcao e necessaria para sempre pegar o ip dinamico para o zookeeper.
        # netifaces.ifaddresses(self.adapter)
        return netifaces.ifaddresses(self.adapter)[netifaces.AF_INET][0]['addr']

    def create_zookeeper_config_file(self):

        subprocess.call("mkdir {}/opt/".format(self.DEFAULT_USER_PATH), shell=True)

        subprocess.call("wget https://downloads.apache.org/zookeeper/zookeeper-3.6.3/apache-zookeeper-3.6.3-bin.tar.gz -P {}/opt/".format(self.DEFAULT_USER_PATH), shell=True)
        subprocess.call("cd && cd {}/opt/ && tar xf apache-zookeeper-3.6.3-bin.tar.gz".format(self.DEFAULT_USER_PATH), shell=True)
        subprocess.call("cd && cd {}/opt/ && ln -s apache-zookeeper-3.6.3-bin zookeeper".format(self.DEFAULT_USER_PATH), shell=True)
        subprocess.call("cd && cd {}/opt/ && rm apache-zookeeper-3.6.3-bin.tar.gz".format(self.DEFAULT_USER_PATH), shell=True)

        new_my_config_file = ZookeeperController.DEFAULT_CONFIG_DATA.replace('NEW_IP', self.get_ip_adapter())
        subprocess.call("echo " + "'{}'".format(new_my_config_file) + " > " + "/opt/zookeeper/conf/zoo.cfg".format(self.DEFAULT_USER_PATH), shell=True)

    @staticmethod
    def get_status():
        cmd = '{}/bin/zkServer.sh status'.format(ZookeeperController.DEFAULT_ZOOKEEPER_PATH)
        return os.popen(cmd).read()

    @staticmethod
    def is_running():
        cmd = ZookeeperController.ZK_CMD.replace('//','/')
        cmd = cmd + ' status'

        return_code = subprocess.run(cmd, shell = True).returncode
        
        if return_code == 0:
            return True
        else:
            return False

    @staticmethod
    def am_i_the_leader():
        cmd = '{}/bin/zkServer.sh status'.format(ZookeeperController.DEFAULT_ZOOKEEPER_PATH)
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
        cmd = "{}/bin/zkServer.sh start".format(ZookeeperController.DEFAULT_ZOOKEEPER_PATH)
        subprocess.call(cmd, shell=True)

    @staticmethod
    def stop_zookeeper_service():
        logging.info("STOPPING ZK")
        cmd = "{}/bin/zkServer.sh stop".format(ZookeeperController.DEFAULT_ZOOKEEPER_PATH)
        subprocess.call(cmd, shell=True)

        #subprocess.call("%s daemon_director.py restart" % sys.executable, shell=True)

    # TODO Há varias etapas redundantes, da pra reduzir pela metade esse metodo.
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

    # TODO H� varias etapas redundantes, da pra reduzir pela metade esse metodo.
    def reset_workers(self):
        logging.info(nowStr() + "Reseting workers...\n")

        logging.info(nowStr() + "\tRemoving tasks... ")
        for t in self.controller_client.zk.get_children('/tasks/'):
            logging.info(nowStr() + "\t\ttask: ", t)
            self.controller_client.zk.delete('/tasks/' + t, recursive=True)
        logging.info(nowStr() + "\tRemoving tasks done. \n")

        logging.info(nowStr() +"\tRemoving experiments from workers... ")
        try:
            for w in self.controller_client.zk.get_children('/registered/workers'):
                logging.info(nowStr() + "\t\tRemoving experiment from worker: ", w)
                for e in self.controller_client.zk.get_children('/registered/workers/' + w + '/torun'):
                    logging.info(nowStr() +"\t\t\tworker: ", w, " children: ", e)
                    self.controller_client.zk.delete('/registered/workers/' + w + '/torun/' + e, recursive=True)
        except:
            pass
        logging.info(nowStr() + "\tRemoving experiments from workers done.\n")

        logging.info(nowStr() + "\tRemoving registered workers... ")
        for w in self.controller_client.zk.get_children('/registered/workers'):
            logging.info(nowStr() + "\t\tregistered worker: ", w)
            self.controller_client.zk.delete('/registered/workers/' + w, recursive=True)
        logging.info(nowStr() + "\tRemoving registered workers done.\n")

        logging.info(nowStr() + "\tRemoving connected busy workers... ")
        for w in self.controller_client.zk.get_children('/connected/busy_workers'):
            logging.info(nowStr() + "\t\tconnected busy worker: ", w)
            self.controller_client.zk.delete('/connected/busy_workers/' + w, recursive=True)
        logging.info(nowStr() + "\tRemoving connected busy workers done.\n")

        logging.info(nowStr() + "\tRemoving connected free workers... ")
        for w in self.controller_client.zk.get_children('/connected/free_workers/'):
            logging.info(nowStr() + "\t\tconnected free worker: ", w)
            self.controller_client.zk.delete('/connected/free_workers/' + w, recursive=True)
        logging.info(nowStr() + "\tRemoving connected free workers done.\n")

        logging.info(nowStr() + "\tRemoving disconnected workers... ")
        for w in self.controller_client.zk.get_children('/disconnected/workers/'):
            logging.info(nowStr() + "\t\tdisconnected worker: ", w)
            self.controller_client.zk.delete('/disconnected/workers/' + w, recursive=True)
        logging.info(nowStr() + "\tRemoving disconnected workers done.\n")

        logging.info(nowStr() + "\tRemoving experiments... ")
        for e in self.controller_client.zk.get_children('/experiments/'):
            logging.info(nowStr() + "\t\t experiment: " + e)
            self.controller_client.zk.delete('/experiments/' + e, recursive=True)
        logging.info(nowStr() + "\tRemoving experiments done.\n")

        logging.info(nowStr() + "Removing done. \n")

    # def kill_daemon_all_registered_workers(self):
    #     print(nowStr(), "\tKilling all worker daemon (python) process... ")
    #     for w in self.controller_client.zk.get_children('/registered/workers'):
    #         try:
    #             print(nowStr(), "\t\tCreating channel with worker: ", w, " ... ", end=' ')
    #             channel = Channel(hostname=w, username=remote_user, password=remote_password, pkey=remote_pkey,
    #                               timeout=30)
    #             print(" done.")
    #             print(nowStr(), "\t\tKilling python process at worker: ", w, " ... ", end=' ')
    #             channel.run("killall python")
    #             print(" done.")
    #
    #         except Exception as e:
    #             print("\n\n")
    #             print(" error while killing worker ", w)
    #             print(e)
    #
    #     print(nowStr(), "\tKilling done. \n")

    def kill_actor_daemon(self, actor):
        print(nowStr(), "\tKilling an actor daemon process... ")
        #for w in self.controller_client.zk.get_children('/registered/workers'):
        try:
            logging.info("\t\tCreating channel with hostname: {} ".format(actor.hostname))
            channel = Channel(hostname=actor.hostname,
                              username=actor.username,
                              password=actor.password,
                              pkey=actor.pkey,
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
            logging.info("%02d:%02d" % (n, count_) + get_tabs(n) + node + get_diff_tabs(n, node) + " : ")
            try:
                value = self.controller_client.zk.get(tree_node)
                #print("\n\n --@@@@-- node '%s' ----" % (node))
                if value is None:
                    logging.info("")
                elif node == "pkey":
                   # print("\n\n --@@aaa@@-- node '%s' ----" % (node))
                    #print("\n\n --@@@@-- node '%s' ----" % (node, value))
                    #value_str = value.to_str()
                    logging.info(" RSA PRIVATE KEY ") #.format(value_str[:5],value_str[-5:]))
                else:

                    # if node == "worker":
                    #     print(value[0][:40], " ...")
                    #     # d = value[0]
                    #     # for k in d.keys():
                    #     #     if k == "pkey":
                    #     #         print("%s : %s" %(k, d[k][0:10]))
                    #     #     else:
                    #     #         print("%s : %s" %(k, d[k]))
                    # else:
                #    print("\n\n\n\ tree_node: %s value: %s" % (tree_node, value[:20]))
                # elif tree_node == "pkey":
                #     print("%s ..." % value[:20])
                # elif tree_node == "worker":
                #     print("asdadsadsa")
                # else:
                    logging.info(value[0])

            except Exception as e:
                logging.error("Exception: {}".format(e))

            try:
                count = 1
                for t in self.controller_client.zk.get_children(tree_node, include_data=False):
                    self.print_zk_tree(tree_node + "/" + t, t, n + 1, count)
                    count += 1
                    # print t

            except Exception as e:
                logging.error("Exception: {}".format(e))

if __name__ == '__main__':
    get_source()