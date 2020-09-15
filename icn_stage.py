#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

__author__ = 'Rafael  '
__email__ = ' @unipampa.edu.br'
__version__ = '{0}.{0}.{5}'
__credits__ = ['PPGA', 'LEA', 'Unipampa@alegrete']

#general bibs
def remote_install_dependences():

    logging.info('+--- Remote dependency installation ---+')
    logging.info('  Updating repositories')
    os.system('sudo apt-get install update')
    logging.info('  Updated repository')
    logging.info('  Checking JAVA-VM')
    os.system('sudo apt-get install default-jre')
    os.system('sudo apt-get install default-jdk')
    logging.info('  Java-VM checked')
    logging.info('  Checking python ')
    os.system('sudo apt-get install python')
    os.system('sudo apt-get install python3')
    os.system('sudo apt-get install python3-pip')
    logging.info('  python checked')
    logging.info('  Checking python-dependences')
    os.system('pip3 install --upgrade pip')
    os.system('pip3 install -r requirements.txt')
    logging.info('+--- Remote dependency installation ---+ DONE')

try:

    import datetime
    import sys
    import json
    import argparse
    import logging
    import subprocess
    import shlex
    import socket
    import struct
    import fcntl
    import os
    import daemon_director
    import tarfile
    import daemon_director
    import threading
    import kazoo
    import paramiko
    import scp
    import netifaces
    import logreset
    import tqdm
    import time
    import math

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
    remote_install_dependences()


# project bibs
from modules.conlib.controller_client import ControllerClient
from modules.conlib.remote_access import Channel
from modules.conlib.controller_client import *
from modules.model.experiment import Experiment
from modules.model.role import Role
from modules.model.worker import Worker
from modules.util.tools import View
from modules.util.tools import Sundry
from zookeeper_controller import ZookeeperController
from experiments_resources import call_tcp_server
from experiments_resources import call_ndn_exp
from experiments_resources import call_ndn_traffic
from time import sleep
from tqdm import trange
#Variables Define
_local_experiments_dir = "./"
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_IPERF_EXPERIMENT_SECS = 60 * 4
DEFAULT_IPERF_INTERVAL_SECS = 5
DEFAULT_IPERF_FILE_OUT = "iperf.out"
DEFAFULT_IPERF_TRANSPORT = "tcp"
_log_level = DEFAULT_LOG_LEVEL
DEFAULT_COMPRESS_FILE = 'icn-stage_compress.tar.gz'
DEFAULT_COMPRESS_PATH = 'icn-stage'
DEFAULT_ZK_CONFIG_PATH = 'apache-zookeeper-3.6.1/conf'
DEFAULT_ICN_STAGE_FILES =['config.json', 'ndn-traffic-client.conf', 'config.json.example', 'play_fibre_ndn.py',
                          'daemon_director_ensemble.py', 'play_mininet_perf_ensambled.py', 'daemon_director.py',
                          'play_mininet_perf.py', 'daemon_worker.py', 'play_mininet_test_tcp.py', 'plot.py',
                          'experiments_resources.py', 'README.md', 'icn_stage.py', 'requirements.txt',
                          'install_director.py', 'settings.json.example', 'install.sh','stage_mininet.py',
                          'Vagrantfile','zookeeper_controller.py']
DEFAULT_ICN_STAGE_PATH =['experiments', 'images', 'results_acm_icn','modules']

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
# Essa parte eh necessAria para a execuCAo em modo ensambled
def get_ip_address(adapter):

    netifaces.ifaddresses(adapter)
    return netifaces.ifaddresses(adapter)[netifaces.AF_INET][0]['addr']
def test_availability_port(address, port):

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    status = sock.connect_ex((address, port))
    sock.close()

    if status == 0:
        return False
    return True
def define_zk_file_config():

    logging.info("+--- Creating Apache-Zookeeper configuration files ---+")
    setting_file = " # Apache-Zookeeper configuration file"
    value_settings = data['settings']
    setting_file += " \n tickTime = " + value_settings['TickTime']
    setting_file += " \n minSessionTimeout = " + value_settings['MinSessionTimeout']
    setting_file += " \n maxSessionTimeout = " + value_settings['MaxSessionTimeout']
    setting_file += " \n initLimit = " + value_settings['InitLimit']
    setting_file += " \n syncLimit = " + value_settings['SyncLimit']
    setting_file += " \n maxClientCnxns = " + value_settings['MaxClientCnxns']

    local_host = get_ip_address(data["zookeeper_adapter"])
    os.system('chmod 777 *')

    for i in data['controllers']:

        if local_host == i['remote_hostname']:

            setting_file += " \n dataDir = " + i['DataDir']
            setting_file += " \n clientPort = " + i['ClientPort']
            setting_file += " \n clientPortAddress = " + i['ClientPortAddress']
            local_path = i['DataDir']
            local_path_zk = local_path.split('/')
            path = local_path_zk[0]
            os.system('chmod 777 *')

            try:

                os.mkdir(local_path_zk[0])
                os.mkdir((local_path_zk[0]+'/'+local_path_zk[1]))

            except:

                print('')

            zk_id = open((local_path_zk[0]+'/'+local_path_zk[1]+'/myid'), "w")
            zk_id.write(i['controller_id'])
            zk_id.close()
            break


    for i in data['controllers']:

        logging.info('+--- Testing available ports for communication ---+\n')
        new_remote_port = i['port']
        new_remote_hostname = i['remote_hostname']
        new_remote_control_id = i['controller_id']
        port_value = int(new_remote_port)

        while (True):

            if test_availability_port(new_remote_hostname, port_value):
                break

            else:

                logging.info(('  Testing available ports for communication Value: ', new_remote_port ))
                port_value += 1

        setting_file += "\nServer." + new_remote_control_id + " = " + str(new_remote_hostname) +\
                        ":" + str(port_value) + ":" + str(port_value + 1000)

        zk_settings = open((DEFAULT_ZK_CONFIG_PATH+'/zoo.cfg'), "w")
        zk_settings.write(setting_file)
        zk_settings.close()

    print('+--- Generating settings file. DONE ---+\n')
    logging.info('+--- Generating settings file. DONE ---+\n')
def compress_stage_dir():

    print('+--- Compressing icn-stage file ---+')
    logging.info('+--- Compressing icn-stage file ---+')
    local_path = os.path.dirname(os.path.realpath(__file__))

    try:
        os.mkdir(DEFAULT_COMPRESS_PATH)

    except:
        print('')

    for i in DEFAULT_ICN_STAGE_FILES:

        os.system(('cp ' + i +' '+DEFAULT_COMPRESS_PATH))

    for i in DEFAULT_ICN_STAGE_PATH:

        os.system(('cp -R ' + i + ' ' + DEFAULT_COMPRESS_PATH))


    with tarfile.open(DEFAULT_COMPRESS_FILE, "w:gz") as tar_file:
            tar_file.add((DEFAULT_COMPRESS_PATH), arcname=os.path.basename((DEFAULT_COMPRESS_PATH)))

    logging.info('+--- Compress DONE. ---+')
def remote_descompress_stage_dir(channel,path_controller):

    logging.info('+--- Remote descompress files. ---+')
    cmd = 'tar -zxf ' + path_controller+'/'+DEFAULT_COMPRESS_FILE
    print(cmd)
    std, err = channel.run('ls')
    print (std.read())
    std, err = channel.run(cmd)

    logging.info('+--- Descompress DONE. ---+')
    logging.debug(std, err)
def remote_send_file(channel,path_controller):

    logging.info('+--- Sending ICN-Stage files. ---+')
    if not channel.put(DEFAULT_COMPRESS_FILE,path_controller):
        logging.info('Error while sending files...Trying again.')
        if not channel.put(DEFAULT_COMPRESS_FILE, path_controller):
            logging.info('Error while sending files')
            return
    logging.info('+--- ICN-Stage DONE. ---+')
def add_controller(max_controllers=None):

    logging.info("+--- Adding Controllers... ---+")
    count = 0
    #compress_stage_dir()
    adapter = data["zookeeper_adapter"]
    for i in data['controllers']:

        info = 'Contacting nodes. HostName: '+i["remote_hostname"]
        logging.info(info)

        count += 1

        channel = Channel(i["remote_hostname"], i["remote_username"],
                          i["remote_password"], pkey=sundry.get_pkey(i["remote_pkey_path"]),timeout=10)

        remote_install(channel, i["remote_username"],adapter,i["controller_id"])
        logging.info("Controller {} added.".format(i["remote_hostname"]))
        logging.debug("max_cotrollers: {} count: {}".format(max_controllers, count))

        if max_controllers is not None and max_controllers == count:
            logging.info("Limit! max_actors: {} count: {}".format(max_controllers, count))
            break

        logging.info('It was not possible to contact the node')

    logging.info("Adding Actors...DONE")
def remote_install(channel,host,adapter,id):

    print('\n+--- Booting remote installer ---+\n')
    local_host = get_ip_address(adapter)

    if not local_host == host:

        controller_path = 'controller_' + str(id)
        info = 'Contacting node ID: '+str(id)+' Address: '+local_host
        logging.info(info)
        logging.debug('Creating remote directories.')
        channel.mkdir(controller_path)
        remote_send_file(channel, controller_path)
        remote_descompress_stage_dir(channel, controller_path)
        cmd = 'python icn-stage.py localconfig '
        channel.run(cmd)
        print('+--- Remote install DONE. ---+')

    else:

        print('')
def director_ensambled_start():

    logging.info('+--- Run Daemon Director Mode: Ensambled')
    logging.info('    +---  Registered directors  ---+')

    for i in data['controllers']:
        logging.info(('Controller: ID: ',data['controller_id'], 'Address: ',data['remote_hostname'], 'Port: ',str(data['ClientPort'])))

##########################################################

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

#remote_install_dependences()
def run_command(zookeeper_controller, command, options=None):

    if command == 'start':
        daemon_director.start()

    if command == 'addcontrollers':
        add_controller(options)

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
    configs = False

    if sys.argv[1] == 'setconfig':

        if len(sys.argv) > 2 and sys.argv[2] == 'ensambled':

            define_zk_file_config()
            logging.info('+---- Config mode: Ensambled ----+')
            exit()
        else:

            logging.info('+---- Config mode: Single ----+')
            configs = True
            exit()

    zookeeper_controller = ZookeeperController(ensambled=configs)

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