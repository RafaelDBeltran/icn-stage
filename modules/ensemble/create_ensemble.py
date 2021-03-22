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
    def __init__(self):                
        self.ANSEMBLE_CONFIG_DATA = '''
        tickTime=2000\n\
        dataDir=/data/zookeeper\n\
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
        '''

        f = open('settings.json')

        data = json.load(f)
        for count, i in enumerate(data['Nodes']): 
            self.ANSEMBLE_CONFIG_DATA = self.ANSEMBLE_CONFIG_DATA.replace('your_zookeeper_node_{}'.format(count + 1), i['remote_host'])


        for count,i in enumerate(data['Nodes']): 

            channel = Channel(hostname=i['remote_host'], username=i['remote_username'],
                    password=i['remote_password'], pkey=sundry.get_pkey(i["remote_pkey_path"]), timeout=_timeout)

            channel.run("sudo mkdir /opt/")
            channel.run("sudo wget https://downloads.apache.org/zookeeper/zookeeper-3.6.2/apache-zookeeper-3.6.2-bin.tar.gz -P /opt/")
            #channel.run("cd && cd /opt/")
            channel.run("cd && cd /opt/ && tar xf apache-zookeeper-3.6.2-bin.tar.gz")
            channel.run("cd && cd /opt/ && ln -s apache-zookeeper-3.6.2-bin zookeeper")
            channel.run("cd && cd /opt/ && rm apache-zookeeper-3.6.2-bin.tar.gz")
            channel.run("echo " + "'{}'".format(self.ANSEMBLE_CONFIG_DATA) + " > " + "/opt/zookeeper/conf/zoo.cfg")
        
            channel.run("rm -rf /data/zookeeper/ ")
            channel.run("mkdir -p /data/zookeeper")
            print("echo {} > /data/zookeeper/myid".format(i['remote_id']))
            channel.run("echo {} > /data/zookeeper/myid".format(i['remote_id']))
            channel.run("bash /opt/zookeeper/bin/zkServer.sh stop")
            time.sleep(7)
            channel.run("bash /opt/zookeeper/bin/zkServer.sh start")
        f.close() 