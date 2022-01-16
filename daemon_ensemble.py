#!/usr/bin/env python3

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
from retry import retry
from datetime import datetime

pattern = "(follower|leader)"
DEFAULT_LOG_LEVEL = logging.INFO
_log_level = DEFAULT_LOG_LEVEL

from kazoo.client import KazooClient
import numpy
#from datetime import datetime
import sys
sys.path.insert(0,'..')
#from extralib.daemon import Daemon
from modules.extralib.daemon import Daemon
#from zookeeper_controller import ZookeeperController

currentdir = os.path.dirname(os.path.realpath(__file__))

DEFAULT_SLEEP_SECONDS = 60
LOG_LEVEL = logging.DEBUG
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_SLEEP_CHECKING = 10

if LOG_LEVEL == logging.DEBUG:
    logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')
else:
    logging.basicConfig(format='%(asctime)s %(message)s',
                datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')

def get_ip_adapter(adapter):

    return ni.ifaddresses(adapter)[ni.AF_INET][0]['addr']

def detect_my_role(hp,port):
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    role = None

    sk.connect((hp,port))
    sk.send(b'srvr')
    role = sk.recv(1024)
    role = role.decode('utf-8')

    if role.find("leader") != -1: 
        return "leader"
    else:
        return "follower"


    # role = re.search(pattern, role)

    # return role.group()

DEFAULT_IP_ADDRESS = get_ip_adapter('enp0s8')

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
        
cmd = "ssh minion@192.168.133.84 \"" + " echo \"$(date +%Y%m%d%H%M.%S) {}\" >> file.dat".format(DEFAULT_IP_ADDRESS)  + "\""

class DirectorEnsembleDaemon(Daemon):

    def __init__(self, pidfile, stdin='/dev/null', stdout='/tmp/ensemble_1.stdout', stderr='/tmp/ensemble_1.stderr'):

        super().__init__(pidfile, stdin=stdin, stdout=stdout, stderr=stderr)
    
    #@retry()   
    def run(self):
        
        while True:
            self.role = detect_my_role(DEFAULT_IP_ADDRESS,2181)
            p = subprocess.Popen(['pgrep', '-f', 'icn-stage.py'], stdout=subprocess.PIPE)
            out, err = p.communicate()
            print(out)
            print(self.role)

            #lógica funcionando
            if (self.role == 'leader') and (out != b''):
                logging.info('Sou o leader, sacou malandragem')
                #p = subprocess.run(" echo \"$(date +%Y%m%d%H%M.%S) {}\" >> file.dat".format(DEFAULT_IP_ADDRESS), shell=True, capture_output=True)
                now = datetime.now()       
                f = open("/home/minion/logs/file.dat", "wa")         
                f.write("{} {}".format(now.strftime("%d/%m/%Y %H:%M:%S"), DEFAULT_IP_ADDRESS))
                f.close()
                logging.info( 'exit status: ' +  p.returncode )
                logging.info( 'stdout: ' + p.stdout.decode() )
                logging.info( 'stderr: ' + p.stderr.decode() )
            elif (self.role == 'leader') and (out == b''):
                try:                    
                    subprocess.call("bash run_icn-stage.sh", shell=True, cwd=currentdir)
                    #subprocess.call("python3 /home/minion/icn-stage/icn-stage.py", shell=True)
                    logging.info('Sou o lider e iniciei o icn-stage')
                except:
                    logging.info('Erro ao iniciar o icn-stage')
            elif (self.role != 'leader') and (out != b''):
                subprocess.call("sleep 30s; kill {} ".format(out.decode('utf-8')), shell=True)
                logging.info('Sou o seguidor e não sou mais continuo')
            else:
                logging.info('Sou o seguidor')


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

    if _log_level == logging.DEBUG:

        logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                            datefmt=TIME_FORMAT, level=_log_level)

    else:

        logging.basicConfig(format='%(asctime)s %(message)s',
                            datefmt=TIME_FORMAT, level=_log_level)

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

        # while(True):
        #     #time.sleep(2.5)
        #     # process_status = subprocess.Popen("ps aux | grep daemon_ensemble.py", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #     # for line in process_status.stdout.readlines():
        #     #     if "daemon_ensemble.py" in line.decode('utf-8'):
        #     #         break
        #     #     else:
        #     #         director_ensemble.start()
        #     p = subprocess.Popen(['pgrep', '-f', 'daemon_ensemble.py'], stdout=subprocess.PIPE)
        #     out, err = p.communicate()

        #     if len(out.strip()) == 0:
        #         director_ensemble.start()
        #     else:
        #         break



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