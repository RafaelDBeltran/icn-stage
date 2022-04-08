import json
import os, sys, subprocess
try:
    currentdir = os.path.dirname(os.path.realpath(__file__))
    parentdir = os.path.dirname(currentdir)
    sys.path.append(parentdir)
    from conlib.remote_access import Channel
    from util.tools import Sundry
    from daemon_ensemble import DirectorEnsembleDaemon
except:
    print('Import error')    
import time

pid_file = "/tmp/daemon_director_ensemble_%s.pid" % '1'
stdout = "/tmp/daemon_director_ensemble_%s.stdout" % '1'
stderr = "/tmp/daemon_director_ensemble_%s.stderr" % '1'

ICN_STAGE_FOLDER = '/icn'

sundry = Sundry()
_timeout = 2
class Ensemble:
    DEFAULT_USER_PATH = ICN_STAGE_FOLDER
    def __init__(self, default_action = None):                
        self.ANSEMBLE_CONFIG_DATA = '''
        tickTime=2000\n\
        dataDir={}/data/zookeeper\n\
        clientPort=2181\n\
        4lw.commands.whitelist=*\n\
        maxClientCnxns=10000000\n\
        initLimit=120\n\
        syncLimit=120\n\
        standaloneEnabled=true\n\
        admin.enableServer=true\n\
        server.1=your_zookeeper_node_1:2888:3888\n\
        server.2=your_zookeeper_node_2:2888:3888\n\
        server.3=your_zookeeper_node_3:2888:3888\n\
        '''.format(self.DEFAULT_USER_PATH)

        f = open('config.json')

        data = json.load(f)
        for count, i in enumerate(data['Nodes']): 
            self.ANSEMBLE_CONFIG_DATA = self.ANSEMBLE_CONFIG_DATA.replace('your_zookeeper_node_{}'.format(count + 1), i['remote_hostname'])


        for count,i in enumerate(data['Nodes']): 

            if sundry.get_ip_adapter(data['zookeeper_adapter']) == i['remote_hostname']:

                subprocess.run("mkdir {}/opt/".format(self.DEFAULT_USER_PATH), shell=True)
                subprocess.run("wget https://dlcdn.apache.org/zookeeper/zookeeper-3.7.0/apache-zookeeper-3.7.0-bin.tar.gz -P {}/opt/".format(self.DEFAULT_USER_PATH), shell=True)
                subprocess.run("cd && cd {}/opt/ && tar xf apache-zookeeper-3.7.0-bin.tar.gz ".format(self.DEFAULT_USER_PATH), shell=True)
                subprocess.run("cd && cd {}/opt/ && ln -s apache-zookeeper-3.7.0-bin zookeeper".format(self.DEFAULT_USER_PATH), shell=True)
                subprocess.run("cd && cd {}/opt/ && rm apache-zookeeper-3.7.0-bin.tar.gz".format(self.DEFAULT_USER_PATH), shell=True)
                subprocess.run("echo " + "'{}'".format(self.ANSEMBLE_CONFIG_DATA) + " > " + "{}/opt/zookeeper/conf/zoo.cfg".format(self.DEFAULT_USER_PATH), shell=True)
                subprocess.run("rm -rf {}/data/zookeeper/ ".format(self.DEFAULT_USER_PATH), shell=True)
                subprocess.run("mkdir -p {}/data/zookeeper".format(self.DEFAULT_USER_PATH), shell=True)
                print("echo {} > {}/data/zookeeper/myid".format(count+1, self.DEFAULT_USER_PATH))
                subprocess.run("echo {} > {}/data/zookeeper/myid".format(count+1, self.DEFAULT_USER_PATH), shell=True)
                if(default_action != None):
                    subprocess.run("bash {}/opt/zookeeper/bin/zkServer.sh stop".format(self.DEFAULT_USER_PATH), shell=True)
                    time.sleep(3)
                    subprocess.run("bash {}/opt/zookeeper/bin/zkServer.sh start".format(self.DEFAULT_USER_PATH), shell=True)
            
            else:
                channel = Channel(hostname=i['remote_hostname'], username=i['remote_username'],
                        password=i['remote_password'], pkey=sundry.get_pkey(i["remote_pkey_path"]), timeout=_timeout)

                channel.run("mkdir {}/opt/".format(self.DEFAULT_USER_PATH))
                channel.run("wget https://dlcdn.apache.org/zookeeper/zookeeper-3.7.0/apache-zookeeper-3.7.0-bin.tar.gz -P {}/opt/".format(self.DEFAULT_USER_PATH))
                #channel.run("cd && cd /opt/")
                channel.run("cd && cd {}/opt/ && tar xf apache-zookeeper-3.7.0-bin.tar.gz".format(self.DEFAULT_USER_PATH))
                channel.run("cd && cd {}/opt/ && ln -s apache-zookeeper-3.7.0-bin zookeeper".format(self.DEFAULT_USER_PATH))
                channel.run("cd && cd {}/opt/ && rm apache-zookeeper-3.7.0-bin.tar.gz".format(self.DEFAULT_USER_PATH))
                channel.run("echo " + "'{}'".format(self.ANSEMBLE_CONFIG_DATA) + " > " + "{}/opt/zookeeper/conf/zoo.cfg".format(self.DEFAULT_USER_PATH))
            
                channel.run("rm -rf {}/data/zookeeper/ ".format(self.DEFAULT_USER_PATH))
                channel.run("mkdir -p {}/data/zookeeper".format(self.DEFAULT_USER_PATH))
                print("echo {} > {}/data/zookeeper/myid".format(count+1, self.DEFAULT_USER_PATH))
                channel.run("echo {} > {}/data/zookeeper/myid".format(count+1, self.DEFAULT_USER_PATH))
                if(default_action != None):
                    channel.run("bash {}/opt/zookeeper/bin/zkServer.sh stop".format(self.DEFAULT_USER_PATH))
                    time.sleep(3)
                    channel.run("bash {}/opt/zookeeper/bin/zkServer.sh start".format(self.DEFAULT_USER_PATH))
                    # time.sleep(15)
                    # channel.run("bash /home/minion/icn-stage/modules/ensemble/ensemble.sh 2>err.log 1>out.log")
                #channel.run("python3 daemon_ensemble.py --start ")
                #channel.run("echo `pwd` > path.out ")


        for count,i in enumerate(data['Nodes']): 

            if sundry.get_ip_adapter(data['zookeeper_adapter']) == i['remote_hostname']:

                # daemon_ensemble_instacnce = DirectorEnsembleDaemon(pidfile=pid_file, stdout=stdout, stderr=stderr)
                # daemon_ensemble_instacnce.start()
                # # subprocess.run("bash /home/minion/icn-stage/modules/ensemble/ensemble.sh 2>err.log 1>out.log")
                #python3 /home/minion/icn-stage/daemon_ensemble.py --start

                if (default_action == 'Active-old'):
                    subprocess.call(
                        "bash {}/icn-stage/modules/ensemble/ensemble.sh 2>err.log 1>out.log".format(ICN_STAGE_FOLDER),
                        shell=True)

                elif (default_action == 'Active-new'):
                    subprocess.call(
                        "bash {}/icn-stage/python3 daemon_director_ensemble.py --start".format(ICN_STAGE_FOLDER),
                        shell=True)

            else:

                channel = Channel(hostname=i['remote_hostname'], username=i['remote_username'],
                        password=i['remote_password'], pkey=sundry.get_pkey(i["remote_pkey_path"]), timeout=_timeout)
                if(default_action == 'Active-old'):
                    channel.run("bash {}/icn-stage/modules/ensemble/ensemble.sh 2>err.log 1>out.log".format(ICN_STAGE_FOLDER))

                elif (default_action == 'Active-new'):
                    channel.run(
                        "bash {}/icn-stage/python3 daemon_director_ensemble.py --start".format(ICN_STAGE_FOLDER))
                #channel.run("python3 daemon_ensemble.py --start ")
                #channel.run("echo `pwd` > path.out ")




        f.close() 
