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
#load tools
from modules.util.tools import View
from modules.util.tools import Sundry
#root imports
from zookeeper_controller import ZookeeperController
from experiments_resources import call_tcp_server
from experiments_resources import call_ndn_exp
from experiments_resources import call_ndn_traffic
#Variables Define
_local_experiments_dir = "./"
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_LOG_LEVEL = logging.INFO

DEFAULT_IPERF_EXPERIMENT_SECS = 60 * 4
DEFAULT_IPERF_INTERVAL_SECS = 5
DEFAULT_IPERF_FILE_OUT = "iperf.out"
DEFAFULT_IPERF_TRANSPORT = "tcp"
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


def add_worker(controller_client, max_actors=None):
    logging.info("Adding Actors...")
    count = 0
    for i in data['workers']:
        count += 1

        new_worker = Worker(i["remote_hostname"],
                        i["remote_username"],
                        password=i["remote_password"],
                        actor_id=i["actor_id"],
                        pkey=sundry.get_pkey(i["remote_pkey_path"]))

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


def run_command(zookeeper_controller, command, options=None):

    if command == 'start':
        daemon_director.start()

    elif command == 'stop':
        daemon_director.stop()

    elif command == 'restart':
        daemon_director.restart()

    elif command == 'status':
        daemon_director.status()

    elif command == 'addactors':
        max_actors = None
        if options is not None:
            max_actors = int(options[0])
        zookeeper_controller.set_controller_client()
        add_worker(zookeeper_controller.controller_client, max_actors)

    elif command == 'test':
        logging.info("*** test tcp begin\n")
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
            call_tcp_server(zookeeper_controller.get_ip_adapter(), test_port)
            logging.info("\n")
            logging.info("*** test tcp end!")

        except Exception as e:
            logging.error("Exception: {}".format(e))
            msg = "Hint: don't forget to add actors!"
            logging.error(msg)

    elif command == 'iperf':
        logging.info("*** iperf evaluation begin options: {}\n".format(options))
        zookeeper_controller.set_controller_client()
        try:
            file_out_name = DEFAULT_IPERF_FILE_OUT
            iperf_interval = DEFAULT_IPERF_INTERVAL_SECS
            client_time_secs = str(DEFAULT_IPERF_EXPERIMENT_SECS)
            transport = DEFAFULT_IPERF_TRANSPORT
            if options is not None:
                file_out_name = options[0]
                if len(options) > 1:
                    iperf_interval = options[1]

                if len(options) > 2:
                    client_time_secs = options[2]

                if len(options) > 3:
                    transport = options[3]
                    if transport == "udp":
                        transport = "--udp"
                    else:
                        transport = ""

            file_err_name = "{}.err".format(file_out_name)

            iperf_port = '10005'

            server_time_secs = int(client_time_secs) + 10

            try:
                cmd_iperf = 'iperf --server --window 1024 --port {} --interval {} --format m --time {} {} '.format(iperf_port, iperf_interval, server_time_secs, transport)
                param_iperf = shlex.split(cmd_iperf)
                cmd_ts = 'ts -s'
                param_ts = shlex.split(cmd_ts)
                logging.info("[IPERF] param iperf: {}".format(param_iperf))
                logging.info("[IPERF] param ts   : {}".format(param_ts))

                fout = open(file_out_name, 'w')
                ferr = open(file_err_name, 'w')
                popen_iperf = subprocess.Popen(param_iperf, stdout=subprocess.PIPE)
                popen_ts = subprocess.Popen(param_ts, stdin=popen_iperf.stdout, stdout=fout, stderr=ferr)

                cmd = ['python3', 'iperf_client.py',
                       '--host', zookeeper_controller.get_ip_adapter(),
                       '--port', iperf_port,
                       '--time', client_time_secs,
                       transport]

                # TODO remove the need for a tar.gz
                experiment_skeleton('iperf', cmd, zookeeper_controller.controller_client,
                                    "experiments/iperf/", "iperf.tar.gz")

                logging.info("Waiting... ")
                for i in trange(server_time_secs):
                    sleep(1)
                cmd = "kill {}".format(popen_iperf.pid)
                param = shlex.split(cmd)
                logging.info("Command: {}".format(cmd))
                subprocess.call(param)

            except subprocess.TimeoutExpired as e:
                logging.info("Iperf finished: {}".format(e))

            except Exception as e:
                # if "timed out" in format(e):
                #     logging.info("Iperf finished: {}".format(e))
                # else:
                #     logging.error("Exception: {}".format(e))
                logging.error("Exception: {}".format(e))
                cmd = "sudo kill {} -SIGINT".format(popen_iperf.pid)
                logging.info("Command: {}".format(cmd))
                subprocess.call(cmd)

            logging.info("\n")
            logging.info("*** Iperf evaluation end!")

        except Exception as e:
            logging.error("Exception: {}".format(e))
            msg = "Hint: don't forget to add actors!"
            logging.error(msg)

            cmd = "sudo pkill iperf"
            logging.info("Command: {}".format(cmd))
            subprocess.call(cmd, shell=True)

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
        try:
            cmd = ['python3', 
            'traffic_client.py',
            '{}'.format(zookeeper_controller.get_ip_adapter())]

            experiment_skeleton('ndn_traffic_generator', cmd,
                                zookeeper_controller.controller_client,
                                "experiments/test_traffic/",
                                "test_traffic.tar.gz")
            call_ndn_traffic()
        except Exception as e:
            logging.error("Exception: {}".format(e))
            msg = "Hint: don't forget to add actors!"
            logging.error(msg)

    elif command == 'reset':
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
    zookeeper_controller = ZookeeperController()

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


if __name__ == '__main__':
    sys.exit(main())