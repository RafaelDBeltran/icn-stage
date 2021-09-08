import json
import os, sys
try:
    currentdir = os.path.dirname(os.path.realpath(__file__))
    parentdir = os.path.dirname(currentdir)
    sys.path.append(parentdir)
    from conlib.remote_access import Channel
    from util.tools import Sundry
except:
    print('Import error')    
import time


sundry = Sundry()
_timeout = 2
class Ensemble:
    DEFAULT_USER_PATH = "/home/minion"
    def __init__(self, default_action = None):                
        self.ANSEMBLE_CONFIG_DATA = '''
        tickTime=2000\n\
        dataDir={}/data/zookeeper\n\
        clientPort=2181\n\
        4lw.commands.whitelist=*\n\
        maxClientCnxns=60\n\
        initLimit=10\n\
        syncLimit=5\n\
        standaloneEnabled=true\n\
        admin.enableServer=true\n\
        server.1=your_zookeeper_node_1:2888:3888\n\
        server.2=your_zookeeper_node_2:2888:3888\n\
        server.3=your_zookeeper_node_3:2888:3888\n\
        '''.format(self.DEFAULT_USER_PATH)

        f = open('config.json')

        data = json.load(f)
        for count, i in enumerate(data['Nodes']): 
            self.ANSEMBLE_CONFIG_DATA = self.ANSEMBLE_CONFIG_DATA.replace('your_zookeeper_node_{}'.format(count + 1), i['remote_host'])


        for count,i in enumerate(data['Nodes']): 

            channel = Channel(hostname=i['remote_host'], username=i['remote_username'],
                    password=i['remote_password'], pkey=sundry.get_pkey(i["remote_pkey_path"]), timeout=_timeout)

            channel.run("sudo mkdir {}/opt/".format(self.DEFAULT_USER_PATH))
            channel.run("sudo wget https://downloads.apache.org/zookeeper/zookeeper-3.6.3/apache-zookeeper-3.6.3-bin.tar.gz -P {}/opt/".format(self.DEFAULT_USER_PATH))
            #channel.run("cd && cd /opt/")
            channel.run("cd && cd {}/opt/ && tar xf apache-zookeeper-3.6.3-bin.tar.gz".format(self.DEFAULT_USER_PATH))
            channel.run("cd && cd {}/opt/ && ln -s apache-zookeeper-3.6.3-bin zookeeper".format(self.DEFAULT_USER_PATH))
            channel.run("cd && cd {}/opt/ && rm apache-zookeeper-3.6.3-bin.tar.gz".format(self.DEFAULT_USER_PATH))
            channel.run("echo " + "'{}'".format(self.ANSEMBLE_CONFIG_DATA) + " > " + "{}/opt/zookeeper/conf/zoo.cfg".format(self.DEFAULT_USER_PATH))
        
            channel.run("rm -rf {}/data/zookeeper/ ".format(self.DEFAULT_USER_PATH))
            channel.run("mkdir -p {}/data/zookeeper".format(self.DEFAULT_USER_PATH))
            print("echo {} > {}/data/zookeeper/myid".format(i['remote_id'], self.DEFAULT_USER_PATH))
            channel.run("echo {} > {}/data/zookeeper/myid".format(i['remote_id'], self.DEFAULT_USER_PATH))
            if(default_action != None):
                channel.run("bash {}/opt/zookeeper/bin/zkServer.sh stop".format(self.DEFAULT_USER_PATH))
                time.sleep(3)
                channel.run("bash {}/opt/zookeeper/bin/zkServer.sh start".format(self.DEFAULT_USER_PATH))
                time.sleep(15)
                channel.run("bash /home/minion/opt/icn-stage/modules/ensemble/ensemble.sh 2>err.log 1>out.log")
            #channel.run("python3 daemon_ensemble.py --start ")
            #channel.run("echo `pwd` > path.out ")

        f.close() 
