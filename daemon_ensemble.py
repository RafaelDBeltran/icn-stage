import argparse
import psutil
import time
import logging
import os
import subprocess
import sys
import signal 
import socket
import re
import random
import netifaces as ni


pattern = "(follower|leader)"


from kazoo.client import KazooClient
import numpy
#from datetime import datetime
from modules.extralib.daemon import Daemon
#from zookeeper_controller import ZookeeperController

DEFAULT_SLEEP_SECONDS = 60
LOG_LEVEL = logging.DEBUG
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_IP_ADDRESS = '0.0.0.0'
DEFAULT_SLEEP_CHECKING = 10

if LOG_LEVEL == logging.DEBUG:
    logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')
else:
    logging.basicConfig(format='%(asctime)s %(message)s',
                datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')


def detect_my_role(hp,port):
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    role = None

    sk.connect((hp,port))
    sk.send(b'srvr')
    role = sk.recv(1024)
    role = role.decode('utf-8')
    role = re.search(pattern, role)

    return role.group()

def get_ip_adapter(adapter):

    return ni.ifaddresses(adapter)[ni.AF_INET][0]['addr']

def ping(ip):
    try:
        subprocess.check_output(["ping", "-c", "1", ip])
        return True                      
    except subprocess.CalledProcessError:
        return False

def kill_process(name): 
    try: 
          
        # iterating through each instance of the proess 
        for line in os.popen("ps ax | grep " + name + " | grep -v grep"):  
            fields = line.split() 
              
            # extracting Process ID from the output 
            pid = fields[0]  
              
            # terminating process  
            os.kill(int(pid), signal.SIGKILL)  
        print("Process Successfully terminated") 
          
    except: 
        print("Error Encountered while running script")

def get_process_status():
    process_status = subprocess.Popen("ps aux | grep icn-stage.py", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in process_status.stdout.readlines():
        if "python3 icn-stage.py" in line.decode('utf-8'):
            return True
        else:
            pass
    
    return False
        
    

class DirectorEnsembleDaemon(Daemon):

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):

        super().__init__(pidfile, stdin=stdin, stdout=stdout, stderr=stderr)
        
    def run(self):
        
        while True:
            self.role = detect_my_role(DEFAULT_IP_ADDRESS,2181)

            self.role_path = "/zookeeper/roles/{}".format(get_ip_adapter('enp0s8'))

            self.zk = KazooClient(hosts = DEFAULT_IP_ADDRESS+':2181')
            self.zk.start()

            if self.zk.exists(self.role_path):
                self.zk.set(self.role_path, str.encode(self.role))

            else:
                self.zk.ensure_path("/zookeeper/roles")
                self.zk.create(self.role_path, str.encode(self.role))


            if self.role == 'leader':
                self.my_dict = {}

                for i in self.zk.get_children("/zookeeper/roles/"):
                    data, _ = self.zk.get("/zookeeper/roles/{}".format(i))
                    if data != b'leader':
                        
                        self.my_dict[i] = data

                        self.res = key, val = random.choice(list(self.my_dict.items())) 
                        print(self.res)
                        if self.zk.exists("/zookeeper/roles/{}/status".format(self.res[0])):
                            self.zk.set("/zookeeper/roles/{}/status".format(self.res[0]), b'1')
                        else:
                            self.zk.ensure_path("/zookeeper/roles/{}/status/".format(self.res[0]))
                            self.zk.create("/zookeeper/roles/{}/status".format(self.res[0]), b'1')

                        for i in list(self.my_dict.items()):
                            if i != self.res:
                                print(i)
                                if self.zk.exists("/zookeeper/roles/{}/status".format(i[0])):
                                    self.zk.set("/zookeeper/roles/{}/status".format(i[0]), b'0')
                                else:
                                    self.zk.ensure_path("/zookeeper/roles/{}/status/".format(i[0]))
                                    self.zk.create("/zookeeper/roles/{}/status/".format(i[0]), b'0')

                while True:
                    if ping(self.res[0]):
                        print("Success")
                        time.sleep(5)
                    else:
                        break
            
            else:
                while True:
                    self.my_dict = {}

                    for i in self.zk.get_children("/zookeeper/roles/"):
                        data, _ = self.zk.get("/zookeeper/roles/{}".format(i))
                        self.my_dict[i] = data
                        self.res = key, val = random.choice(list(self.my_dict.items())) 
                        for i in list(self.my_dict.items()):
                            current_ip = get_ip_adapter('enp0s8')
                            if i != self.res and i[0] == current_ip:
                                current_data, _ = self.zk.get("/zookeeper/roles/{}/status/".format(current_ip))
                                
                                if current_data == b'1' and get_process_status() == True:
                                    #Subprocess que executa o icn-stage
                                    print("########### I am the choice one")
                                    pass
                                elif current_data == b'1' and get_process_status() == False:
                                    print("########### I am the choice one: start thats nowwwww")
                                elif current_data == b'0' and get_process_status() == True:
                                    try:
                                        kill_process("icn_stage.py")
                                        print("########### I'm not the choice one")
                                    except:
                                        pass
                                else:
                                    print("########### Not to do")
                                    pass
                                    
                                


 

def main():

    # parser = argparse.ArgumentParser(description='Daemon Director Ensemble')
    # help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
    # parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)
    # help_msg = "unique id (str), required for running multiple daemons on the host"
    # parser.add_argument("--id", "-i", help=help_msg, default="default", type=str)
    # help_msg = "loop sleep seconds (int)"
    # parser.add_argument("--sleep", "-s", help=help_msg, default=DEFAULT_SLEEP_SECONDS, type=int)
    # parser.add_argument('--start', required=False)
    # parser.add_argument('--stop', required=False)
    # parser.add_argument('--restart', required=False)
    # parser.add_argument('--status', required=False)
    # args = parser.parse_args()

    # if args.log == logging.DEBUG:

    #     logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
    #                         datefmt=TIME_FORMAT, level=args.log)

    # else:

    #     logging.basicConfig(format='%(asctime)s %(message)s',
    #                         datefmt=TIME_FORMAT, level=args.log)

    # logging.info("")
    # logging.info("INPUT")
    # logging.info("---------------------")
    # logging.info("\t logging level : %s" % args.log)
    # logging.info("\t unique id     : %s" % args.id)
    # logging.info("\t sleep secs    : %s" % args.sleep)
    # logging.info("")

    pid_file = "/tmp/daemon_director_ensemble_%s.pid" % '1'
    stdout = "/tmp/daemon_director_ensemble_%s.stdout" % '1'
    stderr = "/tmp/daemon_director_ensemble_%s.stderr" % '1'
    __stdin = open('input_daemon.txt','w')
    __stdin.close()

    logging.info("FILES")
    logging.info("---------------------")
    logging.info("\t pid_file      : %s" % pid_file)
    logging.info("\t stdout        : %s" % stdout)
    logging.info("\t stderr        : %s" % stderr)
    logging.info("")

    if sys.argv[1] == '--start':

        director_ensemble = DirectorEnsembleDaemon(pidfile=pid_file, stdout=stdout, stderr=stderr)
        #director_ensemble.set_sleep_secs(args.sleep)
        director_ensemble.start()

    elif sys.argv[1] == '--stop':

        director_ensemble = DirectorEnsembleDaemon(pidfile=pid_file, stdout=stdout, stderr=stderr)
        #director_ensemble.set_sleep_secs(args.sleep)
        director_ensemble.stop()

    elif sys.argv[1] == '--restart':

        director_ensemble = DirectorEnsembleDaemon(pidfile=pid_file, stdout=stdout, stderr=stderr)
        #director_ensemble.set_sleep_secs(args.sleep)
        director_ensemble.restart()

    # elif sys.argv[1] == '--status':

    #     director_ensemble = DirectorEnsembleDaemon(pidfile=pid_file, stdout=stdout, stderr=stderr)
    #     director_ensemble_pid = director_ensemble.getpid()

    #     if not director_ensemble_pid:

    #         logging.info("director ensemble  (id='%s') isn't running" % (args.id))

    #     else:

    #         logging.info("director ensemble (id='%s') is running [PID=%d]" % (args.id, director_ensemble_pid))

if __name__ == '__main__':
    sys.exit(main())