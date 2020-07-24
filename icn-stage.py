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
try:
    import kazoo
    import paramiko
    import scp
    from tqdm import trange


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
from modules.util.tools import ConfigHelper
from modules.util.tools import View
from modules.util.tools import Sundry
#root imports
from zookeeper_controller import Zookeeper_Controller
from experiments_resources import call_tcpserver
#Variables Define
_local_experiments_dir = "./"
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
sundry = Sundry()
#Load config file
data = json.load(open('config.json'))

Instance_FixIP = ConfigHelper()
Instance_FixIP.create_zookeeper_config_file()

logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                            datefmt=TIME_FORMAT,filename='new_controller.info',level=logging.INFO)


def add_worker(controller_client):
    logging.info("Adding Workers...")
    for i in data['workers']:
        controller_client.task_add(COMMANDS.NEW_WORKER, worker=Worker(i["remote_hostname"], i["remote_username"], password=i["remote_password"], pkey=sundry.get_pkey(i["remote_pkey_path"])))
        logging.info("Worker {} added.".format(i["remote_hostname"]))
    for i in trange(120):
        sleep(1)
    logging.info("Adding Workers...DONE")


# TODO Adicionar loading time no add workers
def experiment_skeleton(experiment_name, commands, experiment_file_name, experiment_dir, controller_client, func = None):
    logging.info("\t Executing experiment {} \t".format(experiment_name))

    experiment_name = 'http_test_%s' % datetime.datetime.now().strftime(TIME_FORMAT).replace(':','-').replace(',','-')

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

    #You can pass a function has a argument if your want run anything in this side of the experimente. If not keep this like None
    if func == None:
        pass
    else:
        func()

    controller_client.config_stop
    logging.info("\tExperiment done.\n")


def help_msg():
    return '''
    Available commands
    ------------------
    start   : 
    stop    :
    restart :
    status  :
    towork  :
    test    :
    help, ? : prints this message
    print   :
    printc  :
    printd  :
    '''


def run_command(zc, command):

    if command == 'start':
        zc.zookeeper_start()
    elif command == 'stop':
        zc.zookeeper_stop()
    elif command == 'restart':
        zc.zookeeper_restart()
    elif command == 'status':
        zc.zookeeper_status()
    elif command == 'towork':
        add_worker(zc.controller_client)
    elif command == 'test':
        try:
            experiment_skeleton('first fly', ['python {}'.format('tcp_client.py'),
                                              '--host {}'.format(Instance_FixIP.get_ip_adapter()),
                                              '--port {}'.format('10000')],
                                "test_tcp.tar.gz", "experiments/test_tcp/", zc.controller_client)

            # TODO o call_tcpserver deveria funcionar sendo chamado dentro do experiment_skeleton
            call_tcpserver(Instance_FixIP.get_ip_adapter(), 10000)

        except:
            msg = "Don't forget to add the workers!"
            logging.error(msg)
            print(msg)

    elif command == 'reset':
        for i in data['workers']:
            zc.kill_worker_daemon(i["remote_username"], i["remote_password"],
                                  sundry.get_pkey(i["remote_pkey_path"]))
            zc.reset_workers()

    elif command == 'printc':
        try:
            root = "/connected/"
            zc.print_zk_tree(root, root, 0)

        except:
            pass
        # zc.controller_client.zk.stop()
        # sys.exit(0)

    elif command == 'printd':
        try:
            root = "/disconnected/"
            zc.print_zk_tree(root, root, 0)

        except:
            pass
        # zc.controller_client.zk.stop()
    # sys.exit(0)

    elif command == 'print':
        try:
            if len(sys.argv) > 2:
                root = sys.argv[2]
                # print root, "/" + root.split("/")[len(root.split("/")) - 1]
                zc.print_zk_tree(root, root, 0)
            else:
                zc.print_zk_tree("/", "/", 0)

        except:
            pass
        # zc.controller_client.zk.stop()
        # sys.exit(0)

    elif command == 'exit' or command == 'quit':
        subprocess.call("fixNoNodeError.sh", shell=True)
        subprocess.call("clean.sh", shell=True)
        print('Goodbye!')
        sys.exit()

    elif command == 'help' or command == '?':
        print(help_msg())

    else:
        print("Command '%s' is not recognized"%command)
        print(help_msg())


def main():

    # Initialize the Zookeeper Controller (API)
    zc = Zookeeper_Controller()

    if len(sys.argv) > 1:
        # single command mode
        command = sys.argv[1]
        run_command(zc, command)

    else:
        # interactive mode
        # Initialize view
        view = View()
        view.print_view()
        while True:
            command = input('ICN-Stage >> ')
            run_command(zc, command)


if __name__ == '__main__':
    sys.exit(main())