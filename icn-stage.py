#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

__author__ = 'Rafael  '
__email__ = ' @unipampa.edu.br'
__version__ = '{0}.{0}.{5}'
__credits__ = ['PPGA', 'LEA', 'Unipampa@Alegrete']

#general bibs
import sys

import json
import argparse
import datetime
import logging
import subprocess
from time import sleep

# specific bibs
import daemon_director

try:
    import kazoo
    import paramiko
    import scp
    from tqdm import trange
    import logreset

except ImportError as error:
    print(error)
    print()
    print("1. Setup a virtual environment: ")
    print("  python3 - m venv ~/Python3env/icn-stage ")
    print("  source ~/Python3env/icn-stage/bin/activate ")
    print()
    print("2. Install requirements:")
    print("  pip3 install --upgrade pip")
    print("  pip3 install -r requirements.txt ")

    print()
    sys.exit(-1)

# project bibs
from modules.conlib.controller_client import ControllerClient
from modules.conlib.remote_access import Channel
from modules.conlib.controller_client import *
from modules.model.experiment import Experiment
from modules.model.role import Role
from modules.model.worker import Worker
#load tools
from modules.util.tools import View
from modules.util.tools import Sundry
#root imports
from zookeeper_controller import ZookeeperController
from experiments_resources import call_tcpserver
#Variables Define
_local_experiments_dir = "./"
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_LOG_LEVEL = logging.INFO
_log_level = DEFAULT_LOG_LEVEL
sundry = Sundry()
#Load config file
data = json.load(open('config.json'))

def set_logging(level=DEFAULT_LOG_LEVEL):

    logreset.reset_logging()
    _log_level = level
    if _log_level == logging.DEBUG:
        logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                            datefmt=TIME_FORMAT, level=_log_level)

    else:
        logging.basicConfig(format='%(asctime)s %(message)s',
                            datefmt=TIME_FORMAT, level=_log_level)

    print("current log level: %d (DEBUG=%d, INFO=%d)" % (_log_level, logging.DEBUG, logging.INFO))


def add_worker(controller_client):
    logging.info("Adding Actors...")
    for i in data['workers']:
        new_worker = Worker(i["remote_hostname"],
                        i["remote_username"],
                        password=i["remote_password"],
                        actor_id=i["actor_id"],
                        pkey=sundry.get_pkey(i["remote_pkey_path"]))

        controller_client.task_add(COMMANDS.NEW_WORKER, worker=new_worker)
        logging.info("Actor {} added.".format(i["remote_hostname"]))
    for i in trange(120):
        sleep(1)
    logging.info("Adding Actors...DONE")


# TODO Add loading time while adding workers
def experiment_skeleton(experiment_name, commands, experiment_file_name, experiment_dir, controller_client, func=None):
    logging.info("\t Executing experiment {} \t".format(experiment_name))

    experiment_name = '%s_%s' % (experiment_name, datetime.datetime.now().strftime(TIME_FORMAT).replace(':','-').replace(',','-'))

    logging.info("\t Experiment_name: {}\t".format(experiment_name))
    logging.info("\t Experiment comands: {}\t".format(' '.join(str(x) for x in commands)))

    simple_role = Role(experiment_name, ' '.join(str(x) for x in commands), 1)
    roles = [simple_role]

    dir_source = _local_experiments_dir + experiment_dir
    sundry.compress_dir(dir_source, experiment_file_name)
    logging.info("Sending experiment... ")
    experiment_ = Experiment(name=experiment_name, filename=experiment_file_name, roles=roles, is_snapshot=False)
    logging.debug("Experiment %s", experiment_)
    
    controller_client.task_add(COMMANDS.NEW_EXPERIMENT, experiment=experiment_)
    logging.debug("\tSending experiment done.\n")

    #You can pass a function as an argument if you need to run anything in this experiment side
    if func == None:
        pass
    else:
        func()

    logging.info("\tExperiment done.\n")


def help_msg():
    return '''
    Available commands
    ------------------
    start    : 
    stop     :
    restart  :
    status   :
    addactors:
    test     :
    help, ?  : prints this message
    print    :
    printc   :
    printd   :
    reset    : clean zookeeper tree
    verbosity: setup logging verbosity level (default=%d, current=%d)
    ''' %(DEFAULT_LOG_LEVEL, _log_level)

# TODO migrate commands to the following syntax
# def help_msg():
#     return '''
#     [COMMNAND] [ARGUMENT]
#     Available commands
#     ------------------
#       COMMAND     ARGUMENTS
#       start     {director, actors, all, ?}                :
#       stop      {director, actors, all, ?}                :
#       restart   {director, actors, all, ?}                : stop; start
#       status    {director, actors, zookeeper, all, ?}
#       clean                                               : clean the zookeeper tree
#       test      {tcp, ndn, ?}                             : basic connectivity tests using stage_mininet.py
#       help, ?   {COMMANDS}                                : prints this message
#       verbosity {10, 20}                                  : setup logging verbosity level (default=%d, current=%d)
#     ''' %(DEFAULT_LOG_LEVEL, _log_level)


def run_command(zookeeper_controller, command):

    if command == 'start':
        daemon_director.start()

    elif command == 'stop':
        daemon_director.stop()

    elif command == 'restart':
        daemon_director.restart()

    elif command == 'status':
        daemon_director.status()

    elif command == 'addactors':
        zookeeper_controller.set_controller_client()
        add_worker(zookeeper_controller.controller_client)

    elif command == 'test':
        zookeeper_controller.set_controller_client()
        try:
            experiment_skeleton('test_tcp', ['python {}'.format('tcp_client.py'),
                                              '--host {}'.format(zookeeper_controller.get_ip_adapter()),
                                              '--port {}'.format('10000')],
                                "test_tcp.tar.gz", "experiments/test_tcp/",
                                zookeeper_controller.controller_client,
                                call_tcpserver(zookeeper_controller.get_ip_adapter(), 10000))

        except Exception as e:
            logging.error("Exception: {}".format(e))
            msg = "Hint: don't forget to add actors!"
            logging.error(msg)

    elif command == 'reset':
        zookeeper_controller.set_controller_client()
        for i in data['workers']:
            zookeeper_controller.kill_worker_daemon(i["remote_username"], i["remote_password"],
                                                    sundry.get_pkey(i["remote_pkey_path"]))
            zookeeper_controller.reset_workers()

    elif command == 'printc':
        zookeeper_controller.set_controller_client()
        try:
            root = "/connected/"
            zookeeper_controller.print_zk_tree(root, root, 0)

        except Exception as e:
            logging.error("Exception: {}".format(e))

    elif command == 'printd':
        zookeeper_controller.set_controller_client()
        try:
            root = "/disconnected/"
            zookeeper_controller.print_zk_tree(root, root, 0)

        except Exception as e:
            logging.error("Exception: {}".format(e))

    elif command == 'print':
        zookeeper_controller.set_controller_client()
        try:
            if len(sys.argv) > 2:
                root = sys.argv[2]
                # print root, "/" + root.split("/")[len(root.split("/")) - 1]
                zookeeper_controller.print_zk_tree(root, root, 0)
            else:
                zookeeper_controller.print_zk_tree("/", "/", 0)

        except Exception as e:
            logging.error("Exception: {}".format(e))

    elif command == 'exit' or command == 'quit':
        subprocess.call("fixNoNodeError.sh", shell=True)
        subprocess.call("clean.sh", shell=True)
        logging.info('Goodbye!')
        sys.exit()

    elif command == 'help' or command == '?':
        print(help_msg())

    elif command.split(' ')[0] == 'log' or command.split(' ')[0] == 'verbosity' or command.split(' ')[0] == 'v':
        try:
            command_option = int(command.split(' ')[1])
            set_logging(command_option)

        except Exception as e:
            logging.error(" Logging verbosity level value invalid '%s'" % command )

    else:
        logging.error("Command '%s' is not recognized" % command)
        print(help_msg())


def main():
    set_logging()
    # Initialize the Zookeeper Controller (API)
    zookeeper_controller = ZookeeperController()

    if len(sys.argv) > 1:
        # single command mode
        command = sys.argv[1]
        run_command(zookeeper_controller, command)

    else:
        # interactive mode
        # Initialize view
        view = View()
        view.print_view()
        while True:
            command = input('ICN-Stage >> ')
            run_command(zookeeper_controller, command)


if __name__ == '__main__':
    sys.exit(main())