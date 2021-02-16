import argparse
import psutil
import time
import logging
import os
import subprocess
import sys

from datetime import datetime
from modules.extralib.daemon import Daemon
from zookeeper_controller import ZookeeperController

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


def zookeeper_is_running():

    process_status = [ proc for proc in psutil.process_iter() if proc.name() == 'zkServer.sh']

    if process_status:

        return True

    else:

        return False

process_PID_s = 9999999

def daemon_controller_is_running(valor):

    if psutil.pid_exists(valor):

        return True

    else:

        return False


def run_daemon_controller(arg_, control_id,ip_):


    if arg_=='start':
    
    	subprocess.call("python3 daemon_director.py start --ip "+ip_ +" --id "+control_id, shell=True)
      
    try:

        file_s = open('/tmp/daemon_director_'+control_id+'.pid','r')

        return int(file_s.read())

    except:

        return -1

def stop_daemon_controller(pid_Ps):

    os.system(('sudo pkill '+pid_Ps))


class DirectorEnsembleDaemon(Daemon):

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', ip_address=DEFAULT_IP_ADDRESS, control_id = 0):

        super().__init__(pidfile, stdin=stdin, stdout=stdout, stderr=stderr)
        
        self.zookeeper_controller = ZookeeperController(ensemble=True, ip_address=ip_address)
        self.sleep_secs = DEFAULT_SLEEP_SECONDS
        self.value_controller_id = control_id
        self.value_controller_ip = ip_address

    def set_sleep_secs(self, sleep_secs):

        self.sleep_secs = sleep_secs

    def run(self):

        process_ss=0000

        while True:

            file_ = open('log_info_status.log','a')
            

            if self.zookeeper_controller.am_i_the_leader():

                file_.write(str(datetime.now())[11:20]+' ServerManager PID:  (My Status) LEADER\n')



                if not daemon_controller_is_running(process_ss):
			
                    file_.write('          DaemonDirector não está rodando. Inicializando...\n')
                    file_.write( str(self.value_controller_id)+str(self.value_controller_ip))
                    process_ss = int(run_daemon_controller("start", self.value_controller_id, self.value_controller_ip))
                    file_.write(('Novo processo DaemonDirector PID: '+str(process_ss)+'\n\n'))
                    file_.close()

                else:
                
                    file_.write(('          DaemonDirector está rodando PID: '+str(process_ss)+'\n\n'))
                    file_.close()

            else:
            
                logging.info('\n(MY Status) FOLLOWER\n')
                file_.write(str(datetime.now())[11:20]+' ServerManager PID:  (My Status) FOLLOWER\n')

                if daemon_controller_is_running(process_ss):

                    file_.write(('          DaemonDirector está rodando PID: '+str(process_ss)+'Parando processo\n\n'))
                    file_.close()
                    stop_daemon_controller(process_ss)

                else:

                    file_.write('          DaemonDirector não está rodando.\n\n')
                    file_.close()

            time.sleep(DEFAULT_SLEEP_CHECKING)


def main():

    parser = argparse.ArgumentParser(description='Daemon Director Ensemble')
    help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
    parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)
    help_msg = "unique id (str), required for running multiple daemons on the host"
    parser.add_argument("--id", "-i", help=help_msg, default="default", type=str)
    help_msg = "loop sleep seconds (int)"
    parser.add_argument("--sleep", "-s", help=help_msg, default=DEFAULT_SLEEP_SECONDS, type=int)
    parser.add_argument('--start', action='store', dest='ip_address', default=DEFAULT_IP_ADDRESS, required=False)
    parser.add_argument('--stop', required=False)
    parser.add_argument('--restart', required=False)
    parser.add_argument('--status', required=False)
    args = parser.parse_args()

    if args.log == logging.DEBUG:

        logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                            datefmt=TIME_FORMAT, level=args.log)

    else:

        logging.basicConfig(format='%(asctime)s %(message)s',
                            datefmt=TIME_FORMAT, level=args.log)

    logging.info("")
    logging.info("INPUT")
    logging.info("---------------------")
    logging.info("\t logging level : %s" % args.log)
    logging.info("\t unique id     : %s" % args.id)
    logging.info("\t sleep secs    : %s" % args.sleep)
    logging.info("")

    pid_file = "/tmp/daemon_director_ensemble_%s.pid" % args.id
    stdout = "/tmp/daemon_director_ensemble_%s.stdout" % args.id
    stderr = "/tmp/daemon_director_ensemble_%s.stderr" % args.id
    __stdin = open('input_daemon.txt','w')
    __stdin.close()

    logging.info("FILES")
    logging.info("---------------------")
    logging.info("\t pid_file      : %s" % pid_file)
    logging.info("\t stdout        : %s" % stdout)
    logging.info("\t stderr        : %s" % stderr)
    logging.info("")

    if sys.argv[1] == '--start':

        director_ensemble = DirectorEnsembleDaemon(pidfile=pid_file, stdout=stdout, stderr=stderr, ip_address=args.ip_address, control_id=args.id)
        director_ensemble.set_sleep_secs(args.sleep)
        director_ensemble.start()

    elif sys.argv[1] == '--stop':

        director_ensemble = DirectorEnsembleDaemon(pidfile=pid_file, stdout=stdout, stderr=stderr)
        director_ensemble.set_sleep_secs(args.sleep)
        director_ensemble.stop()

    elif sys.argv[1] == '--restart':

        director_ensemble = DirectorEnsembleDaemon(pidfile=pid_file, stdout=stdout, stderr=stderr)
        director_ensemble.set_sleep_secs(args.sleep)
        director_ensemble.restart()

    elif sys.argv[1] == '--status':

        director_ensemble = DirectorEnsembleDaemon(pidfile=pid_file, stdout=stdout, stderr=stderr)
        director_ensemble_pid = director_ensemble.getpid()

        if not director_ensemble_pid:

            logging.info("director ensemble  (id='%s') isn't running" % (args.id))

        else:

            logging.info("director ensemble (id='%s') is running [PID=%d]" % (args.id, director_ensemble_pid))

if __name__ == '__main__':
    sys.exit(main())
