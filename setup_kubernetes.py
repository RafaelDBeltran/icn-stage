try:
    from kubernetes import client, config
    import subprocess
    import sys
    from os.path import exists as file_exists
    import argparse
    import socket
    import multiprocessing
    import subprocess
    import datetime
    import tarfile
    import os
    import logging
    import json
    import shlex
    import glob
    from tqdm import tqdm
    from time import sleep

except ImportError as error:
	print(error)
	print()
	print("1. (optional) Setup a virtual environment: ")
	print("  python3 -m venv ~/Python3venv/icnstage ")
	print("  source ~/Python3venv/icnstage/bin/activate ")
	print()
	print("2. Install requirements:")
	print("  pip3 install --upgrade pip")
	print("  pip3 install -r requirements.txt ")
	print()
	sys.exit(-1)

LOG_LEVEL = logging.DEBUG
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_SLEEP_SECONDS = 5

ZK_VERSION="zookeeper-3.8.0"
DEFAULT_QTY_DIRECTORS = 3
DEFAULT_QTY_ACTORS = 3

SLEEP_SECS_PER_POD = 10

config.load_kube_config()
ZK_DIR = "/icn/zookeeper/"
ZK_DATA_DIR = ZK_DIR + "data"

ZK_TICK_TIME = 2000
ZK_SINGLE_CONFIG_DATA= '''
tickTime={}
dataDir={}
clientPort=2181
'''.format(ZK_TICK_TIME, ZK_DATA_DIR)

ZK_ENSEMBLE_CONFIG_DATA = '''
tickTime={}\n\
dataDir={}\n\
clientPort=2181\n\
initLimit=120\n\
syncLimit=120\n\
'''.format(ZK_TICK_TIME, ZK_DATA_DIR)
#4lw.commands.whitelist=*\n\
#maxClientCnxns=10000000\n\
#initLimit=120\n\
#syncLimit=120\n\
#standaloneEnabled=true\n\
#admin.enableServer=true\n\
# server.1=your_zookeeper_node_1:2888:3888\n\
# server.2=your_zookeeper_node_2:2888:3888\n\
# server.3=your_zookeeper_node_3:2888:3888\n\

def run_cmd(cmd_str, shell=False):
    logging.debug("Cmd_str: {}".format(cmd_str))
    # transforma em array por questões de segurança -> https://docs.python.org/3/library/shlex.html
    cmd_array = shlex.split(cmd_str)
    logging.debug("Cmd_array: {}".format(cmd_array))
    if '*' in cmd_str:
        cmd_array_glob = []
        files = []
        for str in cmd_array:
            logging.debug("\tstr: {}".format(str))
            if '*' in str:
                files += glob.glob(str)
                logging.debug("\t\tfiles: {}".format(files))
            else:
                cmd_array_glob += [str]
        if len(files) > 0 :
            for f in files:
                logging.debug("Cmd_array_glob: {}".format(cmd_array_glob+[f]))
                subprocess.run(cmd_array_glob+[f], check=True, shell=shell)
        else:
            logging.debug("None file found.")

    else:
        # executa comando em subprocesso
        subprocess.run(cmd_array, check=True, shell=shell)

def run_cmd_get_output(cmd_str, shell=False):
    logging.debug("Cmd_str: {}".format(cmd_str))
    # transforma em array por questões de segurança -> https://docs.python.org/3/library/shlex.html
    cmd_array = shlex.split(cmd_str)
    result = subprocess.run(cmd_array, check=True, stdout=subprocess.PIPE)
    logging.debug("result std_err: {}".format(result.stderr))
    logging.debug("result std_out: {}".format(result.stdout))
    return str(result.stdout)

def run_cmd_kubernete(pod, cmd_str):
    logging.debug("\tPod: {} Command: {}".format(pod, cmd_str))
    subprocess.run('kubectl exec -it {} -- /bin/bash -c "{}"'.format(pod, cmd_str), shell=True)


def install_zookeeper():
    bin_name = "apache-{}-bin".format(ZK_VERSION)
    tar_name = "{}.tar.gz".format(bin_name)
    if not file_exists(tar_name):
        #"https://dlcdn.apache.org/zookeeper/zookeeper-3.7.0/apache-zookeeper-3.7.0-bin.tar.gz "
        #"https://dlcdn.apache.org/zookeeper/zookeeper-3.7.0/zookeeper-3.7.0-bin.tar.gz"
        run_cmd("wget https://dlcdn.apache.org/zookeeper/{}/{} ".format(ZK_VERSION, tar_name))

    
    run_cmd("tar xf {}".format(tar_name))
    run_cmd("rm -rf zookeeper ")
    run_cmd("mv {} zookeeper ".format(bin_name))
    run_cmd("mkdir -p zookeeper/data")




def get_deployment_file_name(type_, id):
    return "deployment_{}{}.yaml_".format(type_, id)
   

def create_deployment_file(type, id):
    metadata_name = "{}{}".format(type, id)
    container_name = type

    deployment_data = '''
apiVersion: v1
kind: Pod
metadata:
    name: {}
    labels:
        app: ubuntu
        
spec:
    containers:
      - name: {}
        image: rafabeltran/icn-stage:v2-teste
        command: ["/bin/sleep", "3650d"]
        imagePullPolicy: IfNotPresent
        ports:
            - containerPort: 22
              name: ssh
            - containerPort: 2181
              name: zookeeper
            - containerPort: 2888
              name: ensemble1
            - containerPort: 3888
              name: ensemble2
    restartPolicy: Always
    
    '''.format(metadata_name, container_name)
    f = open(get_deployment_file_name(type, id), 'w')
    f.write(deployment_data)
    f.close()


# def run_setup(local_pods):
#     Diretores = {}
#     Atores = {}
#     Auxiliares = {}
#
#     Diretores_count = 1
#     Atores_count = 1
#     Auxiliares_count = 1
#
#     user = 'icn_user'
#     password = 'icn_user'
#
#     v1 = client.CoreV1Api()
#
#     ret = v1.list_pod_for_all_namespaces(watch=False)
#     for i in ret.items:
#         if 'director' in i.metadata.name:
#             Diretores[i.metadata.name] = i.status.pod_ip
#         elif 'actor' in i.metadata.name:
#             Atores[i.metadata.name] = i.status.pod_ip
#         elif 'auxiliar' in i.metadata.name:
#             Auxiliares[i.metadata.name] = i.status.pod_ip
#         else:
#             pass
#
#     config = '''{\"zookeeper_adapter\": \"eth0\",\n
#     "Nodes": [\n
#     '''
#     print("Creating config files...")
#     print("\tDirectors:")
#     for key, value in Diretores.items():
#         print("\t\tkey: {} \t value: {}".format(key, value))
#         if Diretores_count > 1:
#             config += ','
#         config +=  '{\"remote_id\": \"'+str(Diretores_count)+\
#                    '\",\n\"remote_hostname\": \"'+value+\
#                    '\",\n\"remote_username\": \"icn_user\",\n' \
#                    '\"remote_password\": \"icn_user\",\n' \
#                    '\"remote_pkey_path\": \"/icn/keys/id_rsa\",\n' \
#                    '\"Function": \"'+key+'\"} \n'
#         Diretores_count += 1
#     config += '''\n],
#     \"workers\":[
#     '''
#
#     print("\tActors:")
#     for key, value in Atores.items():
#         if Atores_count > 1:
#             config += ','
#         print("\t\tkey: {} \t value: {}".format(key, value))
#         config +=  '{\"actor_id\": \"'+str(Atores_count)+\
#                    '\",\n\"remote_hostname\": \"'+value+\
#                    '\",\n\"remote_username\": \"icn_user\",\n' \
#                    '\"remote_password\": \"icn_user\",\n' \
#                    '\"remote_pkey_path\": \"/icn/keys/id_rsa\",\n' \
#                    '\"Function": \"'+key+'\"}\n'
#         Atores_count += 1
#     config += '''\n]'''
#
#     config += '\n}'
#     # print(config)
#     text_file = open("config.json", "w")
#     text_file.write(config)
#     text_file.close()
#
#     print("\n\n\n")
#     print("Setting config...")
#     print("\tDirectors:")
#
#
#     zk_config_data = ZK_ENSEMBLE_CONFIG_DATA
#     count = 0
#     for key, value in Diretores.items():
#         count += 1
#         zk_config_data += "server.{}={}:2888:3888\n".format(count, value)
#     zk_config_file = open("zookeeper/conf/zoo.cfg", 'w')
#     zk_config_file.write(zk_config_data)
#     zk_config_file.close()
#
#     count = 0
#     for key, _ in Diretores.items():
#         count += 1
#         print("\t\tkey: {} \t value: {}".format(key, _))
#         #'wget https://dlcdn.apache.org/zookeeper/zookeeper-3.8.0/apache-zookeeper-3.8.0-bin.tar.gz'
#         subprocess.run('kubectl cp config.json {}:/icn/icn-stage/'.format(key),shell=True) #{}:/icn/icn-stage
#         subprocess.run('kubectl cp icn-stage/ {}:/icn/'.format(key), shell=True)
#         subprocess.run('kubectl exec -it {} -- /bin/bash -c "sudo /etc/init.d/ssh start"'.format(key),shell=True)
#
#         subprocess.run('kubectl cp zookeeper/ {}:/icn/'.format(key), shell=True)
#         subprocess.run('kubectl exec -it {} -- /bin/bash -c "echo {} > zookeeper/data/myid"'.format(key, count), shell=True)
#         subprocess.run('kubectl exec -it {} -- /bin/bash -c "zookeeper/bin/zkServer.sh stop"'.format(key), shell=True)
#         subprocess.run('kubectl exec -it {} -- /bin/bash -c "zookeeper/bin/zkServer.sh start"'.format(key), shell=True)
#
#
#
#
#     print("\tActors:")
#     for key, _ in Atores.items():
#         print("\t\tkey: {} \t value: {}".format(key, _))
#         subprocess.run('kubectl cp icn-stage/ {}:/icn/'.format(key), shell=True)
#         subprocess.run('kubectl exec -it {} -- /bin/bash -c "sudo /etc/init.d/ssh start"'.format(key),shell=True)
#
#
#     # print("\tController:")
#     # subprocess.run('kubectl cp config.json controlador:/icn/playground',shell=True)
#     # subprocess.run('cp config.json playground',shell=True)


def run_setup(local_pods):
    Diretores = {}
    Atores = {}
    Auxiliares = {}

    Diretores_count = 1
    Atores_count = 1
    Auxiliares_count = 1

    user = 'icn_user'
    password = 'icn_user'
    config_itens = {}
    v1 = client.CoreV1Api()

    logging.debug("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        logging.debug("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
        for k in local_pods.keys():
            if k in i.metadata.name:
                if k not in config_itens.keys():
                    config_itens[k] = []
                
                config_itens[k] += [i.metadata.name]

    logging.debug(config_itens)
    logging.info("Creating config.json file...")
    config_text = '''{\n"zookeeper_adapter\": \"eth0\",\n'''

    for key in config_itens.keys():
        config_text +='''"{}": ['''.format(key)

        for count, value in enumerate(config_itens[key]):
            if count > 0:
                config_text += ''','''
                
            config_text += '''\n\t{\n'''
            config_text += '''\t"remote_id"       : "{}" ,\n'''.format(count+1)
            config_text += '''\t"remote_hostname" : "{}" ,\n'''.format(value)
            config_text += '''\t"Function"        : "{}" ,\n'''.format(key)
            config_text += '''\t"remote_username" : "icn_user",\n'''
            config_text += '''\t"remote_password" : "icn_user",\n'''
            config_text += '''\t"remote_pkey_path": "/icn/keys/id_rsa",\n'''
            config_text += '''\t}'''

        config_text += "]\n"
        
    config_file = open("config.json", "w")
    config_file.write(config_text)
    config_file.close()
    logging.info("Creating ICN-Stage config.json file... DONE!")


    logging.info("Creating ZK zoo.cfg file...")
    ensemble_mode = False
    if len(config_itens['director']) == 1:
        zk_config_data = ZK_SINGLE_CONFIG_DATA
    else:
        ensemble_mode = True
        zk_config_data = ZK_ENSEMBLE_CONFIG_DATA
        for count, value in enumerate(config_itens['director']):
            zk_config_data += "server.{}={}:2888:3888\n".format(count+1, value)

    zk_config_file = open("zookeeper/conf/zoo.cfg", 'w')
    zk_config_file.write(zk_config_data)
    zk_config_file.close()
    logging.info("Creating ZK zoo.cfg file... DONE!")

    logging.info("Configuring pods... DONE!")
    for group in config_itens.keys():
        for count, pod in enumerate(config_itens[group]):
            logging.debug("\tgroup: {} \t pod: {} count: {}".format(group, pod, count))
            run_cmd('kubectl cp icn-stage/ {}:/icn/'.format(pod))
            run_cmd_kubernete(pod, "sudo /etc/init.d/ssh start")

            if group == 'director':
                run_cmd('kubectl cp config.json {}:/icn/icn-stage/'.format(pod))  # {}:/icn/icn-stage
                run_cmd('kubectl cp zookeeper/ {}:/icn/'.format(pod))
                run_cmd_kubernete(pod, "echo {} > zookeeper/data/myid".format(count+1))
                run_cmd_kubernete(pod, ZK_DIR+"/bin/zkServer.sh stop")
                run_cmd_kubernete(pod, ZK_DIR+"/bin/zkServer.sh start")

                if ensemble_mode:
                    cmd_director = "python3 /icn/icn-stage/daemon_director_ensemble.py"
                else:
                    cmd_director = "python3 /icn/icn-stage/daemon_director.py"

                run_cmd_kubernete(pod, cmd_director + " stop")
                run_cmd_kubernete(pod, cmd_director + " start")
             
    logging.info("Configuring pods... DONE!")


def main():
    # arguments
    parser = argparse.ArgumentParser(description='ICN Stage - Setup Helper - Kubernetes')

    help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
    parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

    mode_choices = ['local', 'fibre', 'edgenet'] #the first option is the default
    help_msg = "mode {}".format(mode_choices)
    parser.add_argument("--mode", "-m", help=help_msg, choices=mode_choices, default=mode_choices[0],  type=str)
    #parser.add_argument('mode', choices=mode_choices, default=mode_choices[0], required=False)

    help_msg = "Qty. Actors (default={})".format(DEFAULT_QTY_ACTORS)
    parser.add_argument("--actors", "-a", help=help_msg, choices=range(1,101), default=DEFAULT_QTY_ACTORS, type=int)

    help_msg = "Qty. Directors (default={})".format(DEFAULT_QTY_DIRECTORS)
    parser.add_argument("--directors", "-d", help=help_msg,choices=range(1,11), default=DEFAULT_QTY_DIRECTORS, type=int)

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
    ensemble_mode = args.directors > 1
    logging.info("")
    logging.info("INPUT")
    logging.info("---------------------")
    logging.info("\t logging level : %s" % args.log)
    logging.info("\t mode option   : %s" % args.mode)
    logging.info("\t directors     : %s" % args.directors)
    logging.info("\t actors        : %s" % args.actors)
    logging.info("")

    if args.mode == mode_choices[0]: #local
        logging.info("Configuring zookeeper...")
        install_zookeeper()
        logging.info("Removing all deployment files...")
        run_cmd('rm deployment_*')
        local_pods = {'director': args.directors, 'actor': args.actors}
        logging.info("Creating deployment files...")
        for type in local_pods.keys():
            logging.info("\t{}:".format(type))
            for i in range(1, local_pods[type] + 1):
                logging.info("\t\t{}{}".format(type, i))
                create_deployment_file(type, i)
        logging.info("Creating deployment files... DONE!\n\n")


        logging.info("Applying pods...")
        count_changed_pods = 0
        for type in local_pods.keys():
            logging.info("\t{}:".format(type))
            for i in range(1, local_pods[type] + 1):
                file_name = get_deployment_file_name(type, i)
                cmd = 'kubectl apply -f {}'.format(file_name)
                r = run_cmd_get_output(cmd)
                if 'unchanged' in r:
                    pass
                else:
                    count_changed_pods += 1

        if count_changed_pods > 0:
            for i in tqdm(range(0, SLEEP_SECS_PER_POD*count_changed_pods), desc="Waiting pods wakeup..."):
                sleep(1)
        logging.info("Applying pods... DONE!\n\n")


        logging.info("Setup pods...")
        run_setup(local_pods)
        logging.info("Setup pods... DONE!\n\n")

    elif args.mode == mode_choices[1]: #fibre
        logging.warning("TBD mode: {} ".format(args.mode))

    elif args.mode == mode_choices[2]:  # edgenet
        logging.warning("TBD mode: {} ".format(args.mode))

    else:
        logging.error("Invalid mode: {}".format(args.mode))

if __name__ == '__main__':
    sys.exit(main())