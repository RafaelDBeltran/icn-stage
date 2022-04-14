#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

__author__ = 'Rafael  '
__email__ = ' @unipampa.edu.br'
__version__ = '{0}.{0}.{5}'
__credits__ = ['PPGES', 'LEA', 'Unipampa@alegrete']

#general bibs
import sys

import json
import argparse
import datetime
import logging
import subprocess
from time import sleep
import shlex
import multiprocessing
import daemon_director
from tqdm import tqdm

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
import  experiments_resources
from experiments_resources import call_ndn_exp
from experiments_resources import call_ndn_traffic
from experiments_resources import call_ndn_traffic_server
#Variables Define
_local_experiments_dir = "./"
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_LOG_LEVEL = logging.INFO 

DEFAULT_IPERF_EXPERIMENT_SECS = 60 * 4
DEFAULT_IPERF_INTERVAL_SECS = 5
DEFAULT_IPERF_FILE_OUT = "iperf.out"
DEFAFULT_IPERF_TRANSPORT = "tcp"

DEFAULT_NODES_JSON_FILE = "nodes.json"
_log_level = DEFAULT_LOG_LEVEL
sundry = Sundry()
#Load config file
#data = json.load(open('config.json'))


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


def add_worker(controller_client, nodes_json_file=DEFAULT_NODES_JSON_FILE, max_actors=None):
    logging.info("Adding Actors...")
    data = json.load(open(nodes_json_file))

    count = 0
    for i in data['actor']:
        count += 1

        #new_worker = Worker(i["remote_hostname"], i["remote_username"], password=i["remote_password"], actor_id=i["remote_id"], pkey=sundry.get_pkey(i["remote_pkey_path"]))
        #TODO: uso de chaves nao funcional

        new_worker = Worker(i["remote_hostname"], i["remote_username"], password=i["remote_password"],
                            actor_id=i["remote_id"])
        controller_client.task_add(COMMANDS.NEW_WORKER, worker=new_worker)
        logging.info("Actor {} added.".format(i["remote_hostname"]))
        logging.debug("max_actors: {} count: {}".format(max_actors, count))
        if max_actors is not None and max_actors == count:
            logging.info("Limit! max_actors: {} count: {}".format(max_actors, count))
            break


    # for i in trange(100):
    #     sleep(1)
    logging.info("Adding Actors...DONE!")


def experiment_skeleton(experiment_name, commands, controller_client, experiment_dir=None, experiment_file_name=None):
    logging.info("\tExecuting experiment {} \t".format(experiment_name))

    experiment_name = '%s_%s' % (experiment_name, datetime.datetime.now().strftime(TIME_FORMAT).replace(':','-').replace(',','-'))

    logging.info("\tExperiment_name   : {}\t".format(experiment_name))
    logging.info("\tExperiment command: {}\t".format(' '.join(str(x) for x in commands)))
    #cmd_array = shlex.split(cmd_str)
    simple_role = Role(experiment_name, ' '.join(str(x) for x in commands), 1)
    roles = [simple_role]

    dir_source = _local_experiments_dir + experiment_dir
    if experiment_file_name is not None:
        logging.info("\tCompressing dir source '{}' to file '{}".format(dir_source, experiment_file_name))
        sundry.compress_dir(dir_source, experiment_file_name)

    logging.info("\tSending experiment... ")
    experiment_ = Experiment(name=experiment_name, filename=experiment_file_name, roles=roles, is_snapshot=False)
    logging.debug("\tExperiment instantiated %s", experiment_)
    
    controller_client.task_add(COMMANDS.NEW_EXPERIMENT, experiment=experiment_)
    logging.debug("\tSending experiment done.\n")


def help_msg():
    return '''
    Available commands
    ------------------
    addactors           : [max actors] [nodes.json]
    test                : tcp client/server test
    iperf               : file_out_name_str iperf_interval_secs client_time_secs (tcp|udp)
    ndn                 :
    help, h, ?          : prints this message
    print, p            : print zookeeper tree
    printc              : print zookeeper subtree: connected workers
    printd              : print zookeeper subtree: disconnected workers
    reset               : clear zookeeper tree
    reset-tasks         : reset tasks and experiments
    verbosity, log, v, l:  level (default=%d, current=%d)
    ''' %(DEFAULT_LOG_LEVEL, _log_level)

zookeeper_controller = None
def get_zookeeper_controller_singleton():
    global zookeeper_controller
    if zookeeper_controller is None:
        zookeeper_controller = ZookeeperController()
    return zookeeper_controller

def run_command(zookeeper_controller = None, command = None, options=None):
    nodes_json_file = DEFAULT_NODES_JSON_FILE
    if command == 'exit' or command == 'quit':
        # subprocess.call("fixNoNodeError.sh", shell=True)
        # subprocess.call("clean.sh", shell=True)
        logging.info('Goodbye!')
        sys.exit(0)

    elif command == 'help' or command == '?' or command == 'h':
        print(help_msg())

    elif command == 'log' or command == 'verbosity' or command == 'v' or command == 'l':
        try:
            set_logging(int(options[0]))

        except Exception as e:
            logging.error(" Logging verbosity level value invalid {} {}".format(command, options))
            
    else:

        zookeeper_controller = get_zookeeper_controller_singleton()

        if command == 'test':
            logging.info("*** test tcp begin")
            test_port = 10002

            zookeeper_controller.set_controller_client()
            try:
                cmd = ['python3 {}'.format('tcp_client.py'),
                      '--host {}'.format(zookeeper_controller.get_ip_adapter()),
                      '--port {}'.format(test_port)]

                experiment_skeleton('test_tcp', cmd,
                                    zookeeper_controller.controller_client,
                                    "experiments/test_tcp/",
                                    "test_tcp.tar.gz")
                #experiments_resources.call_tcp_server(zookeeper_controller.get_ip_adapter(), test_port)
                # Start bar as a process
                p = multiprocessing.Process(target=experiments_resources.call_tcp_server, args=(zookeeper_controller.get_ip_adapter(), test_port))
                p.start()
                TIMEOUT = 10 #seconds
                SLEEP = 1 #seconds
                print("a")
               # while time.time() - start <= TIMEOUT:
                for i in tqdm(range(int(TIMEOUT/SLEEP)), "Waiting max. {} secs.".format(TIMEOUT)):
                    sleep(SLEEP)
                    if not p.is_alive():
                        break

                # Wait for 10 seconds or until process finishes
               # p.join(10)
                result = "[OK]"
                # If thread is still active
                if p.is_alive():
                    result = "[FAIL]"
                    logging.info("\t server is still waiting... let's kill it...")

                    # Terminate - may not work if process is stuck for good
                    p.terminate()
                    # OR Kill - will work for sure, no chance for process to finish nicely however
                    # p.kill()

                    p.join()


                logging.info("\n")
                logging.info("*** test tcp end! result: {}".format(result))

            except Exception as e:
                logging.error("Exception: {}".format(e))
                msg = "Hint: don't forget to add actors!"
                logging.error(msg)

        elif command == 'ndn':
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
            zookeeper_controller.set_controller_client()
            _timeout = 2
            try:
                logging.debug("nodes_json_file: {}".format(nodes_json_file))
                data = json.load(open(nodes_json_file))
                auxiliar_ip = None

                for auxiliar in data['auxiliars']:

                    auxiliar_ip = auxiliar['remote_hostname']

                    channel = Channel(hostname=auxiliar['remote_hostname'], username=auxiliar['remote_username'],
                            password=auxiliar['remote_password'], pkey=sundry.get_pkey(auxiliar["remote_pkey_path"]), timeout=_timeout)

                    channel.put('./experiments/test_traffic/low.conf', 'low.conf')
                    channel.put('./experiments/test_traffic/traffic_server.py','traffic_server.py')
                    channel.put('./experiments/test_traffic/ndn-traffic-server.conf','ndn-traffic-server.conf')
                    channel.put('./experiments/test_traffic/run_server.sh','run_server.sh')
                    channel.run('bash run_server.sh')


                sleep(10)
                logging.info(sys.argv[2:])
                logging.info(sys.argv[3:])
                # cmd = ['python3', 'traffic_client.py', auxiliar_ip, '\''+ sys.argv[2:] + '\'','\''+  sys.argv[3:]+ '\'']
                cmd = ['python3', 'traffic_client.py', auxiliar_ip]

                experiment_skeleton('ndn_traffic_generator', cmd,
                                    zookeeper_controller.controller_client,
                                    "experiments/test_traffic/",
                                    "test_traffic.tar.gz")

            except Exception as e:
                logging.error("Exception: {}".format(e))
                msg = "Hint: don't forget to add actors!"
                logging.error(msg)

        elif command == 'traffic2':
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

        elif command == 'addactors':
            logging.debug("nodes_json_file: {}".format(nodes_json_file))

            zookeeper_controller.set_controller_client()
            max_actors = None
            if options is not None:
                max_actors = int(options[0])

            add_worker(controller_client=zookeeper_controller.controller_client, nodes_json_file=nodes_json_file, max_actors=max_actors)
          
        elif command == 'reset':
            zookeeper_controller = get_zookeeper_controller_singleton()
            data = json.load(open(nodes_json_file))
            for i in data['actor']:
                #TODO implementar chave
                # worker = Worker(i["remote_hostname"],
                #                 i["remote_username"],
                #                 password=i["remote_password"],
                #                 pkey=sundry.get_pkey(i["remote_pkey_path"]),
                #                 actor_id=i["actor_id"])
                worker = Worker(i["remote_hostname"],
                                i["remote_username"],
                                password=i["remote_password"],
                                actor_id=i["remote_id"])
                zookeeper_controller.kill_actor_daemon(worker)
            zookeeper_controller.reset_workers()

        elif command == 'reset-tasks':
            zookeeper_controller.reset_tasks()

        elif command == 'printc':
            try:
                root = "/connected/"
                zookeeper_controller.print_zk_tree(root, root, 0)

            except Exception as e:
                logging.error("Exception: {}".format(e))

        elif command == 'printd':
            try:
                root = "/disconnected/"
                zookeeper_controller.print_zk_tree(root, root, 0)

            except Exception as e:
                logging.error("Exception: {}".format(e))

        elif command == 'print' or command == 'p':
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



        else:
            logging.error("Command '%s' is not recognized" % command)
            print(help_msg())


def main():
    set_logging()

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
        while True:
            commands = input('ICN-Stage >> ')
            commands = commands.split(" ")
            command = commands[0]

            options = None
            if len(commands) > 1:
                options = commands[1:]

            logging.debug("command: {} options: {}".format(command, options))
            run_command(zookeeper_controller, command, options)
            
        # # interactive mode
        # # Initialize view
        # view = View()
        # view.print_view()
        # import socket
        # serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # serv.bind((sundry.get_ip_adapter('eth0'), 8081))
        # serv.listen(5)
        # while True:
        #     conn, addr = serv.accept()
        #
        #     while True:
        #         data = conn.recv(4096)
        #         #commands = input('ICN-Stage >> ')
        #         #commands = commands.split(" ")
        #         #command = commands[0]
        #
        #         options = None
        #         #if len(commands) > 1:
        #         #    options = commands[1:]
        #         print(data.decode('utf-8'))
        #         logging.debug("command: {} options: {}".format(data.decode('utf-8'), options))
        #         run_command(zookeeper_controller, data.decode('utf-8'), options)
        #         if data.decode('utf-8') == 'ensemble-start':
        #             conn.send(b'reconnect')
        #         else:
        #             conn.send(b'next')
        #         if not data:
        #             break
        # print('here')
        # conn.close()


if __name__ == '__main__':
    sys.exit(main())