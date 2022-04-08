from kubernetes import client, config
import subprocess
import sys
from os.path import exists as file_exists

ZK_VERSION="zookeeper-3.7.0"
NUM_ACTORS = 3
NUM_DIRECTORS = 3
NUM_PODS = {'actor':NUM_ACTORS, 'director':NUM_DIRECTORS}

config.load_kube_config()
ZK_DATA_DIR = "/icn/zookeeper/data"

ZK_STAND_ALONE_CONFIG_DATA= '''
tickTime=2000
dataDir={}
clientPort=2181
'''.format(ZK_DATA_DIR)

ZK_ENSEMBLE_CONFIG_DATA = '''
tickTime=2000\n\
dataDir={}\n\
clientPort=2181\n\
initLimit=120\n\
syncLimit=120\n\
'''.format(ZK_DATA_DIR)
#4lw.commands.whitelist=*\n\
#maxClientCnxns=10000000\n\
#initLimit=120\n\
#syncLimit=120\n\
#standaloneEnabled=true\n\
#admin.enableServer=true\n\
# server.1=your_zookeeper_node_1:2888:3888\n\
# server.2=your_zookeeper_node_2:2888:3888\n\
# server.3=your_zookeeper_node_3:2888:3888\n\

def install_zookeeper():
    bin_name = "apache-{}-bin".format(ZK_VERSION)
    tar_name = "{}.tar.gz".format(bin_name)
    if not file_exists(tar_name):
        #"https://dlcdn.apache.org/zookeeper/zookeeper-3.7.0/apache-zookeeper-3.7.0-bin.tar.gz "
        #"https://dlcdn.apache.org/zookeeper/zookeeper-3.7.0/zookeeper-3.7.0-bin.tar.gz"
        subprocess.run("wget https://dlcdn.apache.org/zookeeper/{}/{} ".format(
                ZK_VERSION, tar_name), shell=True)

    
    subprocess.run("tar xf {}".format(tar_name), shell=True)
    subprocess.run("rm -rf zookeeper ", shell=True)
    subprocess.run("mv {} zookeeper ".format(bin_name), shell=True)



    subprocess.run("mkdir -p zookeeper/data", shell=True)




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


def run_setup():
    Diretores = {}
    Atores = {}
    Auxiliares = {}

    Diretores_count = 1
    Atores_count = 1
    Auxiliares_count = 1

    user = 'icn_user'
    password = 'icn_user'

    v1 = client.CoreV1Api()

    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        if 'director' in i.metadata.name:
            Diretores[i.metadata.name] = i.status.pod_ip
        elif 'actor' in i.metadata.name:
            Atores[i.metadata.name] = i.status.pod_ip
        elif 'auxiliar' in i.metadata.name:
            Auxiliares[i.metadata.name] = i.status.pod_ip
        else:
            pass

    # print(Diretores)
    # print(Atores)

    config = '''{\"zookeeper_adapter\": \"eth0\",\n
    "Nodes": [\n
    '''
    print("Creating config files...")
    print("\tDirectors:")
    for key, value in Diretores.items():
        print("\t\tkey: {} \t value: {}".format(key, value))
        if Diretores_count > 1:
            config += ','
        config +=  '{\"remote_id\": \"'+str(Diretores_count)+\
                   '\",\n\"remote_hostname\": \"'+value+\
                   '\",\n\"remote_username\": \"icn_user\",\n' \
                   '\"remote_password\": \"icn_user\",\n' \
                   '\"remote_pkey_path\": \"/icn/keys/id_rsa\",\n' \
                   '\"Function": \"'+key+'\"} \n'
        Diretores_count += 1
    config += '''\n],
    \"workers\":[
    '''

    print("\tActors:")
    for key, value in Atores.items():
        if Atores_count > 1:
            config += ','
        print("\t\tkey: {} \t value: {}".format(key, value))
        config +=  '{\"actor_id\": \"'+str(Atores_count)+\
                   '\",\n\"remote_hostname\": \"'+value+\
                   '\",\n\"remote_username\": \"icn_user\",\n' \
                   '\"remote_password\": \"icn_user\",\n' \
                   '\"remote_pkey_path\": \"/icn/keys/id_rsa\",\n' \
                   '\"Function": \"'+key+'\"}\n'
        Atores_count += 1
    config += '''\n]'''

    config += '\n}'
    # print(config)
    text_file = open("config.json", "w")
    text_file.write(config)
    text_file.close()

    print("\n\n\n")
    print("Setting config...")
    print("\tDirectors:")


    zk_config_data = ZK_ENSEMBLE_CONFIG_DATA
    count = 0
    for key, value in Diretores.items():
        count += 1
        zk_config_data += "server.{}={}:2888:3888\n".format(count, value)
    zk_config_file = open("zookeeper/conf/zoo.cfg", 'w')
    zk_config_file.write(zk_config_data)
    zk_config_file.close()
    
    count = 0
    for key, _ in Diretores.items():
        count += 1
        print("\t\tkey: {} \t value: {}".format(key, _))
        #'wget https://dlcdn.apache.org/zookeeper/zookeeper-3.8.0/apache-zookeeper-3.8.0-bin.tar.gz'
        subprocess.run('kubectl cp config.json {}:/icn/icn-stage/'.format(key),shell=True) #{}:/icn/icn-stage
        subprocess.run('kubectl cp icn-stage/ {}:/icn/'.format(key), shell=True)
        subprocess.run('kubectl exec -it {} -- /bin/bash -c "sudo /etc/init.d/ssh start"'.format(key),shell=True)

        subprocess.run('kubectl cp zookeeper/ {}:/icn/'.format(key), shell=True)
        subprocess.run('kubectl exec -it {} -- /bin/bash -c "echo {} > zookeeper/data/myid"'.format(key, count), shell=True)
        subprocess.run('kubectl exec -it {} -- /bin/bash -c "zookeeper/bin/zkServer.sh stop"'.format(key), shell=True)
        subprocess.run('kubectl exec -it {} -- /bin/bash -c "zookeeper/bin/zkServer.sh start"'.format(key), shell=True)




    print("\tActors:")
    for key, _ in Atores.items():
        print("\t\tkey: {} \t value: {}".format(key, _))
        subprocess.run('kubectl cp icn-stage/ {}:/icn/'.format(key), shell=True)
        subprocess.run('kubectl exec -it {} -- /bin/bash -c "sudo /etc/init.d/ssh start"'.format(key),shell=True)


    # print("\tController:")
    # subprocess.run('kubectl cp config.json controlador:/icn/playground',shell=True)
    # subprocess.run('cp config.json playground',shell=True)

def main():
    print("Configuring zookeeper...")
    install_zookeeper()

    print("Creating deployment files...")
    for type in NUM_PODS.keys():
        print("\t{}:".format(type))
        for i in range(1, NUM_PODS[type]+1):
            print("\t\t{}{}".format(type,i))
            create_deployment_file(type,i)
    print("\n\n\n")

    print("Running pods...")
    for type in NUM_PODS.keys():
        print("\t{}:".format(type))
        for i in range(1, NUM_PODS[type]+1):
            file_name = get_deployment_file_name(type, i)
            print("")
            print(file_name)
            cmd = 'kubectl apply -f {}'.format(file_name)

            print(cmd)
            subprocess.run(cmd, shell=True)
    #sleep(30)
    print("\n\n\n")
    run_setup()


if __name__ == '__main__':
    sys.exit(main())