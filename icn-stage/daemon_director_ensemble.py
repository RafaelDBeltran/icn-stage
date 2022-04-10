import argparse
import psutil
import time
import logging
import os
import subprocess
import sys

from modules.extralib.daemon import Daemon
from zookeeper_controller import ZookeeperController

DEFAULT_SLEEP_SECONDS = 0.1
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'


def zookeeper_is_running():
    process_status = [ proc for proc in psutil.process_iter() if proc.name() == 'zkServer.sh']

    if process_status:
        return True
    else:
        return False


def daemon_controller_is_running():
    process_status = [ proc for proc in psutil.process_iter() if proc.name() == 'daemon_director.py']

    if process_status:
        return True
    else:
        return False


def run_daemon_controller(arg_):
    # cmd = [sys.executable, "daemon_director.py", "arg_"]
    # subprocess.call(cmd)
    cmd = "python3 icn-stage/daemon_director.py {}".format(arg_)
    logging.info(cmd)
    subprocess.call(cmd, shell=True)


class DirectorEnsembleDaemon(Daemon):

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', logging=None, log=logging.INFO):
        super().__init__(pidfile, stdin=stdin, stdout=stdout, stderr=stderr)
        self.zookeeper_controller = ZookeeperController()
        self.sleep_secs = DEFAULT_SLEEP_SECONDS
        self.log = log
        

    def stop(self):
        run_daemon_controller("--log {} stop".format(self.log))
        super().stop()

    def set_sleep_secs(self, sleep_secs):
        self.sleep_secs = sleep_secs

    def run(self):
        last_status = None
        status = last_status

        while True:
            if self.zookeeper_controller.am_i_the_leader():
                status = "LEADER"
   
                if not daemon_controller_is_running():
                    logging.debug("daemon_director isn't running\n")
                    run_daemon_controller("--log {} start".format(self.log))

                else:
                    logging.debug("daemon_director is already running!\n")

            else:
                status = "FOLLOWER"
                
                if daemon_controller_is_running():
                    logging.debug("daemon_director is running")
                    logging.debug("We must start daemon_director")
                    run_daemon_controller("--log {} stop".format(self.log))

                else:
                    logging.debug("daemon_director isn't running.\n")

            msg = '(My Status) {}\n'.format(status)
            if last_status == status:
                logging.debug(msg)

            else:
                logging.info(msg)
                last_status = status

            time.sleep(self.sleep_secs)


def main():
    # arguments
    parser = argparse.ArgumentParser(description='Daemon Director Ensemble')

    help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
    parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

    help_msg = "unique id (str), required for running multiple daemons on the host"
    parser.add_argument("--id", "-i", help=help_msg, default="default", type=str)

    help_msg = "loop sleep seconds (float)"
    parser.add_argument("--sleep", "-s", help=help_msg, default=DEFAULT_SLEEP_SECONDS, type=float)

    cmd_choices = ['start', 'stop', 'restart', 'status']
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

    pid_file = "/tmp/daemon_director_ensemble_%s.pid" % args.id
    stdout = "/tmp/daemon_director_ensemble_%s.stdout" % args.id
    stderr = "/tmp/daemon_director_ensemble_%s.stderr" % args.id

    logging.info("FILES")
    logging.info("---------------------")
    logging.info("\t pid_file      : %s" % pid_file)
    logging.info("\t stdout        : %s" % stdout)
    logging.info("\t stderr        : %s" % stderr)
    logging.info("")
 
    director_ensemble = DirectorEnsembleDaemon(pidfile=pid_file, stdout=stdout, stderr=stderr, logging=logging, log=args.log)
    director_ensemble.set_sleep_secs(args.sleep)

    # process input parameters
    if args.cmd == 'start':
        director_ensemble.start()
        #daemon_pid = worker_daemon.getpid()

        # if not daemon_pid:
        # 	logging.info("Unable run daemon")
        # else:
        # 	logging.info("Daemon is running [PID=%d]" % daemon_pid)

    elif args.cmd == 'stop':
        logging.info("Stopping director ensemble")
        director_ensemble.stop()

    elif args.cmd == 'restart':
        logging.info("Restarting director ensemble")
        director_ensemble.restart()

    elif args.cmd == 'status':
        director_ensemble_pid = director_ensemble.getpid()

        if not director_ensemble_pid:
            logging.info("director ensemble  (id='%s') isn't running" % (args.id))
        else:
            logging.info("director ensemble (id='%s') is running [PID=%d]" % (args.id, director_ensemble_pid))


if __name__ == '__main__':
    sys.exit(main())