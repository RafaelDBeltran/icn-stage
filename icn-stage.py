#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

__author__ = 'Rafael  '
__email__ = ' @unipampa.edu.br'
__version__ = '{0}.{0}.{5}'
__credits__ = ['PPGA', 'LEA', 'Unipampa@alegrete']

#general bibs
import sys

import json
import argparse
import datetime
import logging
import subprocess
from time import sleep
import shlex
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
from modules.ensemble.create_ensemble import Ensemble
#load tools
from modules.util.tools import View
from modules.util.tools import Sundry
#root imports
from zookeeper_controller import ZookeeperController
from experiments_resources import call_tcp_server
from experiments_resources import call_ndn_exp
from experiments_resources import call_ndn_traffic
from experiments_resources import call_ndn_traffic_server
#Variables Define
_local_experiments_dir = "./"
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_LOG_LEVEL = logging.DEBUG

DEFAULT_IPERF_EXPERIMENT_SECS = 60 * 4
DEFAULT_IPERF_INTERVAL_SECS = 5
DEFAULT_IPERF_FILE_OUT = "iperf.out"
DEFAFULT_IPERF_TRANSPORT = "tcp"
_log_level = DEFAULT_LOG_LEVEL
sundry = Sundry()
#Load config file
data = json.load(open('config.json'))
Ensemble_status = False
Ensemble_zookeeper_controller = None

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


def add_worker(controller_client, max_actors=None):
    logging.info("Adding Actors...")
    count = 0
    for i in data['workers']:
        count += 1

        new_worker = Worker(i["remote_hostname"], i["remote_username"], password=i["remote_password"], actor_id=i["actor_id"], pkey=sundry.get_pkey(i["remote_pkey_path"]))

        controller_client.task_add(COMMANDS.NEW_WORKER, worker=new_worker)
        logging.info("Actor {} added.".format(i["remote_hostname"]))
        logging.debug("max_actors: {} count: {}".format(max_actors, count))
        if max_actors is not None and max_actors == count:
            logging.info("Limit! max_actors: {} count: {}".format(max_actors, count))
            break


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
    addactors: max actors
    test     :
    iperf    : file_out_name_str iperf_interval_secs client_time_secs (tcp|udp)
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


def run_command(zookeeper_controller = None, command = None, options=None):

    if command == 'start':
        daemon_director.start()

    elif command == 'stop':
        daemon_director.stop()

    elif command == 'restart':
        daemon_director.restart()

    elif command == 'status':
        daemon_director.status()

    elif command == 'addactors':
        zookeeper_controller = ZookeeperController()
        zookeeper_controller.set_controller_client()
        max_actors = None
        if options is not None:
            max_actors = int(options[0])
        
        add_worker(zookeeper_controller.controller_client, max_actors)

    elif command == 'test':
        logging.info("*** test tcp begin\n")
        test_port = 10002
        zookeeper_controller = ZookeeperController()
        zookeeper_controller.set_controller_client()
        try:
            cmd = ['python3 {}'.format('tcp_client.py'),
                  '--host {}'.format(zookeeper_controller.get_ip_adapter()),
                  '--port {}'.format(test_port)]

            experiment_skeleton('test_tcp', cmd,
                                zookeeper_controller.controller_client,
                                "experiments/test_tcp/",
                                "test_tcp.tar.gz")
            call_tcp_server(zookeeper_controller.get_ip_adapter(), test_port)
            logging.info("\n")
            logging.info("*** test tcp end!")

        except Exception as e:
            logging.error("Exception: {}".format(e))
            msg = "Hint: don't forget to add actors!"
            logging.error(msg)

    elif command == 'ndn':
        zookeeper_controller = ZookeeperController()
        zookeeper_controller.set_controller_client()
        try:
            cmd = ['python3', 
            'poke.py',
            '{}'.format(zookeeper_controller.get_ip_adapter())]

            experiment_skeleton('test_ndn', cmd,
                                zookeeper_controller.controller_client,
                                "experiments/test_ndn/",
                                "test_ndn.tar.gz")
            call_ndn_exp()
        except Exception as e:
            logging.error("Exception: {}".format(e))
            msg = "Hint: don't forget to add actors!"
            logging.error(msg)

    elif command == 'traffic':
        zookeeper_controller = ZookeeperController()
        zookeeper_controller.set_controller_client()
        _timeout = 2
        try:

            auxiliar_ip = None

            for auxiliar in data['auxiliars']:

                auxiliar_ip = auxiliar['remote_host']

                channel = Channel(hostname=auxiliar['remote_host'], username=auxiliar['remote_username'],
                        password=auxiliar['remote_password'], pkey=sundry.get_pkey(auxiliar["remote_pkey_path"]), timeout=_timeout)
                
                channel.put('./experiments/test_traffic/low.conf', 'low.conf')
                channel.put('./experiments/test_traffic/traffic_server.py','traffic_server.py')
                channel.put('./experiments/test_traffic/ndn-traffic-server.conf','ndn-traffic-server.conf')
                channel.run('sudo python3 /home/vagrant/traffic_server.py &')


            cmd = ['python3', 'traffic_client.py', '{}'.format(auxiliar_ip)]

            experiment_skeleton('ndn_traffic_generator', cmd,
                                zookeeper_controller.controller_client,
                                "experiments/test_traffic/",
                                "test_traffic.tar.gz")

        except Exception as e:
            logging.error("Exception: {}".format(e))
            msg = "Hint: don't forget to add actors!"
            logging.error(msg)

    elif command == 'traffic2':
        zookeeper_controller = ZookeeperController()
        zookeeper_controller.set_controller_client()
        try:
            cmd = ['python3', 
            'ndn_client.py',
            '{}'.format(str(zookeeper_controller.get_ip_adapter()))]

            experiment_skeleton('ndn_traffic_generator2', cmd,
                                zookeeper_controller.controller_client,
                                "experiments/test_traffic2/",
                                "test_traffic2.tar.gz")
            call_ndn_traffic_server(zookeeper_controller.get_ip_adapter(),10000)
        except Exception as e:
            logging.error("Exception: {}".format(e))
            msg = "Hint: don't forget to add actors!"
            logging.error(msg)

    elif command == 'ensemble-start':
        _ = Ensemble(default_action='Active')
        Ensemble_zookeeper_controller = ZookeeperController()
        Ensemble_status = True
        
    elif command == 'reset':
        zookeeper_controller = ZookeeperController()
        zookeeper_controller.set_controller_client()
        for i in data['workers']:

            worker = Worker(i["remote_hostname"],
                            i["remote_username"],
                            password=i["remote_password"],
                            pkey=sundry.get_pkey(i["remote_pkey_path"]),
                            actor_id=i["actor_id"])
            zookeeper_controller.kill_actor_daemon(worker)
        zookeeper_controller.reset_workers()

    elif command == 'reset-tasks':
        zookeeper_controller = ZookeeperController()
        zookeeper_controller.set_controller_client()
        zookeeper_controller.set_controller_client()
        zookeeper_controller.reset_tasks()

    elif command == 'printc':
        zookeeper_controller = ZookeeperController()
        zookeeper_controller.set_controller_client()
        zookeeper_controller.set_controller_client()
        try:
            root = "/connected/"
            zookeeper_controller.print_zk_tree(root, root, 0)

        except Exception as e:
            logging.error("Exception: {}".format(e))

    elif command == 'printd':
        zookeeper_controller = ZookeeperController()
        zookeeper_controller.set_controller_client()
        try:
            root = "/disconnected/"
            zookeeper_controller.print_zk_tree(root, root, 0)

        except Exception as e:
            logging.error("Exception: {}".format(e))

    elif command == 'print':
        zookeeper_controller = ZookeeperController()
        zookeeper_controller.set_controller_client()
        try:

            if options is not None:
                root = "/"
                if len(options) > 0:
                    root = options[0]
                # print root, "/" + root.split("/")[len(root.split("/")) - 1]
                zookeeper_controller.print_zk_tree(root, root, 0)
            else:
                zookeeper_controller.print_zk_tree("/", "/", 0)

        except Exception as e:
            logging.error("Exception: {}".format(e))

    elif command == 'exit' or command == 'quit':
        #subprocess.call("fixNoNodeError.sh", shell=True)
        #subprocess.call("clean.sh", shell=True)
        logging.info('Goodbye!')
        sys.exit(0)

    elif command == 'help' or command == '?':
        print(help_msg())

    elif command == 'log' or command == 'verbosity' or command == 'v':
        try:
            set_logging(options[0])

        except Exception as e:
            logging.error(" Logging verbosity level value invalid {} {}".format(command, options))

    else:
        logging.error("Command '%s' is not recognized" % command)
        print(help_msg())


def main():
    set_logging()
    # Initialize the Zookeeper Controller (API)
    zookeeper_controller = Ensemble_zookeeper_controller

    if len(sys.argv) > 1:
        # single command mode
        command = sys.argv[1]
        options = None
        if len(sys.argv) > 2:
            options = sys.argv[2:]

        run_command(zookeeper_controller, command, options)

    else:
        # interactive mode
        # Initialize view
        view = View()
        view.print_view()
        import socket
        serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serv.bind((sundry.get_ip_adapter('enp0s8'), 8081))
        serv.listen(5)
        while True:
            conn, addr = serv.accept()

            while True:
                data = conn.recv(4096)
                #commands = input('ICN-Stage >> ')
                #commands = commands.split(" ")
                #command = commands[0]

                options = None
                #if len(commands) > 1:
                #    options = commands[1:]
                print(data.decode('utf-8'))
                logging.debug("command: {} options: {}".format(data.decode('utf-8'), options))
                run_command(zookeeper_controller, data.decode('utf-8'), options)
                if not data:
                    break
        print('here')
        conn.close()


if __name__ == '__main__':
    sys.exit(main())