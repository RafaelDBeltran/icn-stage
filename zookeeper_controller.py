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
    for i in range(50 - len(word)):
        s += " "

    # for i in range(8-n):
    #	s += "\t"
    return s


class ZookeeperController:
    DEFAULT_ZOOKEEPER_PATH = "./apache-zookeeper-3.6.1/"
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
    ZK_CMD = ['%s/bin/zkServer.sh' % DEFAULT_ZOOKEEPER_PATH]

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

        self.zookeeper_ip_port = self.get_ip_adapter() + ':2181'
        logging.info("zookeeper_ip_port: {}".format(self.zookeeper_ip_port))
        self.create_zookeeper_config_file()

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


    def get_ip_adapter(self):
        # Como o ip do fibre eh dinamico, essa funcao e necessaria para sempre pegar o ip dinamico para o zookeeper.
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
        cmd = '%s/bin/zkServer.sh status' % ZookeeperController.DEFAULT_ZOOKEEPER_PATH
        return os.popen(cmd).read()

    @staticmethod
    def is_running():
        cmd = ZookeeperController.ZK_CMD
        cmd.append('status')
        return_code = subprocess.run(cmd).returncode
        if return_code == 0:
            return True
        else:
            return False

    @staticmethod
    def am_i_the_leader():
        cmd = '%s/bin/zkServer.sh status'%ZookeeperController.DEFAULT_ZOOKEEPER_PATH
        status = os.popen(cmd).read()
        try:
            if status.index('leader'):
                return True

            else:
                return False

        except:
            return False

    # RM: isso não faz sentido! o controlador do zookeeper deveria controlar apenas o ZK, não o diretor
    # def zookeeper_status(self):
    #     logging.info("STATUS ZK")
    #     subprocess.call("%s daemon_director.py status" % sys.executable, shell=True)
    #
    # def zookeeper_restart(self):
    #     logging.info("RESTART ZK")
    #     subprocess.call("%s daemon_director.py restart" % sys.executable, shell=True)
    #
    # def zookeeper_stop(self):
    #     logging.info("STOP ZK")
    #     subprocess.call("%s daemon_director.py stop" % sys.executable, shell=True)

    @staticmethod
    def start_zookeeper_service():
        logging.info("STARTING ZK")
        cmd = "%s/bin/zkServer.sh start" % ZookeeperController.DEFAULT_ZOOKEEPER_PATH
        subprocess.call(cmd, shell=True)

    @staticmethod
    def stop_zookeeper_service():
        logging.info("STOPPING ZK")
        cmd = "%s/bin/zkServer.sh stop" % ZookeeperController.DEFAULT_ZOOKEEPER_PATH
        subprocess.call(cmd, shell=True)

        #subprocess.call("%s daemon_director.py restart" % sys.executable, shell=True)


    # TODO Há varias etapas redundantes, da pra reduzir pela metade esse metodo.
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
                channel = Channel(hostname=w, username=remote_user, password=remote_password, pkey=remote_pkey,
                                  timeout=30)
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
            print("%02d:%02d" % (n, count_), get_tabs(n), node, get_diff_tabs(n, node), " : ", end=' ')
            try:
                value = self.controller_client.zk.get(tree_node)
                #print("\n\n --@@@@-- node '%s' ----" % (node))
                if value is None:
                    print("")
                elif node == "pkey":
                   # print("\n\n --@@aaa@@-- node '%s' ----" % (node))
                    #print("\n\n --@@@@-- node '%s' ----" % (node, value))
                    #value_str = value.to_str()
                    print(" RSA PRIVATE KEY ") #.format(value_str[:5],value_str[-5:]))
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
                    print(value[0])

            except Exception as e:
                print("Exception: ", e)

            try:
                count = 1
                for t in self.controller_client.zk.get_children(tree_node, include_data=False):
                    self.print_zk_tree(tree_node + "/" + t, t, n + 1, count)
                    count += 1
                    # print t

            except Exception as e:
                print("Exception: ", e)