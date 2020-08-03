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
from iperf3 import iperf3

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
from experiments_resources import call_tcp_server
from experiments_resources import call_ndn_exp
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
    for i in trange(100):
        sleep(1)
    logging.info("Adding Actors...DONE")


# TODO Add loading time while adding workers
def experiment_skeleton(experiment_name, commands, controller_client, experiment_dir=None, experiment_file_name=None):
    logging.info("\t Executing experiment {} \t".format(experiment_name))

    experiment_name = '%s_%s' % (experiment_name, datetime.datetime.now().strftime(TIME_FORMAT).replace(':','-').replace(',','-'))

    logging.info("\t Experiment_name   : {}\t".format(experiment_name))
    logging.info("\t Experiment command: {}\t".format(' '.join(str(x) for x in commands)))

    simple_role = Role(experiment_name, ' '.join(str(x) for x in commands), 1)
    roles = [simple_role]

    dir_source = _local_experiments_dir + experiment_dir
    if experiment_file_name is not None:
        logging.info("Compressing dir source '{}' to file '{}".format(dir_source, experiment_file_name))
        sundry.compress_dir(dir_source, experiment_file_name)

    logging.info("Sending experiment... ")
    experiment_ = Experiment(name=experiment_name, filename=experiment_file_name, roles=roles, is_snapshot=False)
    logging.debug("Experiment instantiated %s", experiment_)
    
    controller_client.task_add(COMMANDS.NEW_EXPERIMENT, experiment=experiment_)
    logging.debug("\tSending experiment done.\n")


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
    iperf    : 
    ndn      :
    help, ?  : prints this message
    print    :
    printc   :
    printd   :
    reset    : clean zookeeper tree
    reset-tasks : reset tasks and experiments
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
#       clean     {all, tasks}                              : clean the zookeeper tree
#       test      {tcp, ndn, ?}                             : basic connectivity tests assuming stage_mininet.py
#       eva       {iperf, ndn, ?}                           : performance evaluation assuming stage_mininet.py
#       help, ?   {COMMANDS}                                : prints this message
#       verbosity {10, 20}                                  : setup logging verbosity level (default=%d, current=%d)
#     ''' %(DEFAULT_LOG_LEVEL, _log_level)


def run_command(zookeeper_controller, command, option=None):

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
        logging.info("*** test tcp begin\n")
        zookeeper_controller.set_controller_client()
        try:
            cmd = ['python {}'.format('tcp_client.py'),
                  '--host {}'.format(zookeeper_controller.get_ip_adapter()),
                  '--port {}'.format('10000')]

            experiment_skeleton('test_tcp', cmd,
                                zookeeper_controller.controller_client,
                                "experiments/test_tcp/",
                                "test_tcp.tar.gz")
            call_tcp_server(zookeeper_controller.get_ip_adapter(), 10000)
            logging.info("\n")
            logging.info("*** test tcp end!")

        except Exception as e:
            logging.error("Exception: {}".format(e))
            msg = "Hint: don't forget to add actors!"
            logging.error(msg)

    elif command == 'iperf':
        logging.info("*** iperf3 begin\n")
        zookeeper_controller.set_controller_client()
        try:
            file_log = "iperf.log"
            if option is not None:
                file_log = option

            iperf_port = '10000'
            interval_secs = '1'
            time_secs = '600'
            cmd = ['python3', 'iperf3_client.py',
             '--client', zookeeper_controller.get_ip_adapter(),
             '--port', iperf_port,
             '--time', time_secs,
             '--udp']

            # TODO remove the need for a tar.gz
            experiment_skeleton('iperf3', cmd, zookeeper_controller.controller_client,
                                "experiments/iperf3/", "iperf3.tar.gz")


            cmd = "iperf3 --server --port {} --interval {} | tee {}".format(iperf_port, interval_secs, time_secs, file_log)
            logging.info("Command: {}".format(cmd))
            subprocess.call(cmd, shell=True)

            logging.info("\n")
            logging.info("*** iperf3 end!")

        except Exception as e:
            logging.error("Exception: {}".format(e))
            msg = "Hint: don't forget to add actors!"
            logging.error(msg)
    
    elif command == 'ndn':
        zookeeper_controller.set_controller_client()
        try:
            experiment_skeleton('test_ndn', ['sudo', 'bash', 'poke.sh'],
                                "test_ndn.tar.gz", "experiments/test_ndn/",
                                zookeeper_controller.controller_client)
            call_ndn_exp()

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
    elif command == 'reset-tasks':
        zookeeper_controller.set_controller_client()
        zookeeper_controller.reset_tasks()

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
            if option is not None:
                root = option
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
        option = None
        if len(sys.argv) > 2:
            option = sys.argv[2]

        run_command(zookeeper_controller, command, option)

    else:
        # interactive mode
        # Initialize view
        view = View()
        view.print_view()
        while True:
            commands = input('ICN-Stage >> ')
            commands = commands.split(" ")
            command = commands[0]
            option = None
            if len(commands)>1:
                option = commands[1]
            run_command(zookeeper_controller, command, option)


if __name__ == '__main__':
    sys.exit(main())