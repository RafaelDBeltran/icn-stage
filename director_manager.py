
__author__ = 'Rafael  '
__email__ = ' @unipampa.edu.br'
__version__ = '{0}.{0}.{5}'
__credits__ = ['PPGA', 'LEA', 'Unipampa@alegrete']

import datetime
import glob
import json
import os
import shlex
import socket
import subprocess
import tarfile
import sys

try:

    import daemon_director
    import kazoo
    import paramiko
    import scp
    import netifaces
    import logreset
    import tqdm

except ImportError as error:

    #install_dependencies()
    pass
    

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

DEFAULT_CREATE_COMPRESS_FILE = True
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_COMPRESS_FILE = 'icn-stage_gz.tar.gz'
DEFAULT_COMPRESS_PATH = 'icn-stage_gz'
DEFAULT_ZK_CONFIG_PATH = 'apache-zookeeper-3.6.1/conf'
DEFAULT_DEPENDENCIES = ['update']
DEFAULT_COMMAND_INSTALL = ['sudo', 'apt-get', 'install']
DEFAULT_COMMAND_UPGRADE_PIP = ['pip3', 'install', '--upgrade', 'pip']
DEFAULT_CMD_INSTALL_WITH_PIP = ['pip3', 'install', '-r', 'requirements.txt']
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'

sundry = Sundry()
data = json.load(open('config.json'))

def set_logging(level=DEFAULT_LOG_LEVEL):

    logreset.reset_logging()
    _log_level = level

    if _log_level == logging.DEBUG:

        logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
	datefmt=TIME_FORMAT, level=_log_level)

    else:

        logging.basicConfig(format='%(asctime)s %(message)s', datefmt=TIME_FORMAT, level=_log_level)
        
    print("current log level: %d (DEBUG=%d, INFO=%d)" % (_log_level, logging.DEBUG, logging.INFO))

def install_dependencies():

    for _ in DEFAULT_DEPENDENCIES:

        cmd = [DEFAULT_COMMAND_INSTALL, DEFAULT_DEPENDENCIES]
        subprocess.run(cmd)

    cmd = DEFAULT_COMMAND_UPGRADE_PIP
    subprocess.run(cmd)
    cmd = DEFAULT_CMD_INSTALL_WITH_PIP
    subprocess.run(cmd)

def test_availability_port(address, port):

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    status = sock.connect_ex((address, port))
    sock.close()

    if status == 0:

        return False

    else:

        return True

def generate_configs_zk(local_host):

    value_settings = data['settings']
    logging.info("+--- Creating Apache-Zookeeper configuration files ---+")
    setting_file = " # Apache-Zookeeper configuration file"
    setting_file += "\ntickTime=" + value_settings['TickTime']
    setting_file += "\nminSessionTimeout=" + value_settings['MinSessionTimeout']
    setting_file += "\nmaxSessionTimeout=" + value_settings['MaxSessionTimeout']
    setting_file += "\ninitLimit=" + value_settings['InitLimit']
    setting_file += "\nsyncLimit=" + value_settings['SyncLimit']
    setting_file += "\nmaxClientCnxns=" + value_settings['MaxClientCnxns']
    setting_file += "\nclientPortAddress="+local_host
    setting_file += "\ndataDir=" + value_settings['DataDir']
    setting_file += "\nclientPort=" + value_settings['ClientPort']

    for i in data['controllers']:

        logging.info('+--- Testing available ports for communication ---+\n')
        new_remote_port = i['port']
        new_remote_hostname = i['remote_hostname']
        new_remote_control_id = i['controller_id']
        port_value = int(new_remote_port)

        while True:

            if test_availability_port(new_remote_hostname, port_value):

                break

            else:

                logging.info(('  Testing available ports for communication Value: ', new_remote_port))
                port_value += 1
                
        setting_file += "\nserver." + new_remote_control_id + "=" + str(new_remote_hostname) + \
                        ":" + str(port_value+int(i['controller_id'])) + ":" + str(port_value + 1000+int(i['controller_id']))

        zk_settings = open((DEFAULT_ZK_CONFIG_PATH + '/zoo.cfg'), "w")
        zk_settings.write(setting_file)
        zk_settings.close()

    print('+--- Generating settings file. DONE ---+\n')
    logging.info('+--- Generating settings file. DONE ---+\n')


def create_zk_data_path():

    data_zk_path = data['settings']['DataDir']
    data_path = data_zk_path.split('/')
    local_temp = ''

    for i in data_path:
    
        os.mkdir(local_temp+i+'/')
        local_temp = i+'/'


def compress_stage_dir():

    logging.info('+--- Compressing icn-stage file ---+')
    os.path.dirname(os.path.realpath(__file__))
    file_list_icn_stage = glob.glob("*")

    try:

        cmd = ['rm', '-rf', DEFAULT_COMPRESS_PATH]
        subprocess.run(cmd)
        os.mkdir(DEFAULT_COMPRESS_PATH)

    except:

        logging.error('Error creating compressed path.')
        sys.exit(-1)


    for i in file_list_icn_stage:


        if os.path.isfile(i) and not i == DEFAULT_COMPRESS_FILE:

            cmd = ['sudo', 'cp', i, DEFAULT_COMPRESS_PATH]
            subprocess.run(cmd)

        elif os.path.isdir(i) and not i == DEFAULT_COMPRESS_PATH:

            cmd = ['sudo', 'cp', '-R', i, DEFAULT_COMPRESS_PATH]

            if not (i == 'ndn-src' or i == 'mininet' or i == 'node_modules'):
                subprocess.run(cmd)
        else:

            logging.debug("skip")
            pass

    with tarfile.open(DEFAULT_COMPRESS_FILE, "w:gz") as tar_file:
    
        tar_file.add(DEFAULT_COMPRESS_PATH, arcname=os.path.basename(DEFAULT_COMPRESS_PATH))

    logging.info('+--- Compress DONE. ---+')
    cmd = 'rm -R ' + DEFAULT_COMPRESS_PATH
    os.system(cmd)

def generate_myid(my_id):

    myid = open(('apache-zookeeper-3.6.1/bin/'+data['settings']['DataDir']+'/myid'), 'w')
    myid.write(str(my_id))
    myid.close()
    myid = open((data['settings']['DataDir']+'/myid'), 'w')
    myid.write(str(my_id))
    myid.close()


def remote_send_file(channel, path_controller):

    logging.info('+--- Sending ICN-Stage files. ---+')
    channel.direct_put(DEFAULT_COMPRESS_FILE, path_controller)
    logging.info('+--- added ---+')


def add_controller():

    logging.info("+--- Adding Controllers... ---+")

    if not os.path.isfile(DEFAULT_COMPRESS_FILE) or DEFAULT_CREATE_COMPRESS_FILE:

        compress_stage_dir()

    else:

        logging.info("tar.gz already exists and DEFAULT_CREATE_COMPRESS_FILE=False")

    for i in data['controllers']:

        info = '\n\nContacting node ID: ' + str(i["controller_id"]) + ' Address: ' + i["remote_hostname"]+'\n'
        logging.info(info)
        
        try:
        
        	channel = Channel(hostname = i["remote_hostname"], username = i["remote_username"],password = i["remote_password"],pkey=sundry.get_pkey(i["remote_pkey_path"]),
        	timeout=10)
        	remote_install(channel, i["controller_id"], i["remote_hostname"])
        	logging.info("Controller {} added.".format(i["remote_hostname"]))
        
        except:
        
        	logging.info('It was not possible to contact the node')

    logging.info("Adding Controls...DONE")


def remote_install(channel, id_machine, local_host):



    remote_path = 'controller_' + str(id_machine)
    logging.debug("remote_path: %s" % remote_path)
    remote_send_file(channel, "~/")
    cmd = 'tar -xvf %s' % DEFAULT_COMPRESS_FILE
    channel.run(cmd)
    cmd = 'mv %s %s ' % (DEFAULT_COMPRESS_PATH, remote_path)
    channel.run(cmd)
    channel.chdir(remote_path)
    cmd = 'python3 director_manager.py createpath '
    channel.run(cmd)
    cmd = 'python3 director_manager.py setconfig %s' %local_host
    channel.run(cmd)
    cmd = 'python3 director_manager.py createid %s' % str(id_machine)
    a,b = channel.run(cmd)
    cmd  = 'chmod +x apache-zookeeper-3.6.1/bin/zkServer.sh'
    a,b = channel.run(cmd)
    print('**************************')
    print(a.read(),b.read())
    print('**************************')



def remote_run(channel, host, id_machine):

    try:

        remote_path = '~/controller_' + str(id_machine)
        logging.info("\t\tchannel changing to remote_path: %s" % remote_path)
        channel.chdir(remote_path)
        logging.info("\t\tdone.")
        cmd = 'python3 daemon_director_ensemble.py --start {} --id {}'.format(host, id_machine)
        logging.info("\t\trunning cmd: {}".format(cmd))
        a, b = channel.run(cmd)
        logging.info("\t\tdone.")
        logging.info("std_out: {}".format(a.read().decode('utf-8')))
        logging.info("std_err: {}".format(b.read().decode('utf-8')))
        
    except Exception as e:

        logging.error("Exception [remote_run]: {}".format(e))


def run_controllers():

    logging.info("+--- Run Controllers... ---+")

    for i in data['controllers']:

        host = i["remote_hostname"]
        info = '\n\nContacting node ID: {} Address: {}\n'.format(str(i["controller_id"]), host)
        logging.info(info)
        
        try:
        	channel = Channel(hostname = i["remote_hostname"], username = i["remote_username"],password = i["remote_password"],pkey=sundry.get_pkey(i["remote_pkey_path"]) ,timeout=10)
        	logging.info("[OK] Channel with {} ".format(host))
        	
        	
        	remote_run(channel, host, i["controller_id"])
        	logging.info("[OK] Controller running at {}".format(host))
 
        except:
 	
        	logging.error('It was not possible to contact the node: {}'.format(host))
        	
    logging.info("Running Controllers... DONE")

def main():

    set_logging()

    if sys.argv[1] == 'setconfig':
        generate_configs_zk(sys.argv[2])

    elif sys.argv[1] == 'createpath':
        create_zk_data_path()

    elif sys.argv[1] == 'createid':
        generate_myid(sys.argv[2])

    elif sys.argv[1] == 'install':
        logging.info('+----Install Config mode: Ensemble ----+')
        add_controller()

    elif sys.argv[1] == 'run':
        logging.info('+----Run Config mode: Ensemble ----+')
        run_controllers()

    else:

        print('Error arguments')


if __name__ == '__main__':
    sys.exit(main())
