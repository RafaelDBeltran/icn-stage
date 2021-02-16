import json
from modules.conlib.remote_access import Channel
from modules.util.tools import Sundry

sundry = Sundry()
_timeout = 2

ansemble_config_data = '''
tickTime=2000\n\
dataDir=/data/zookeeper\n\
clientPort=2181\n\
maxClientCnxns=60\n\
initLimit=10\n\
syncLimit=5\n\
server.1=your_zookeeper_node_1:2888:3888\n\
server.2=your_zookeeper_node_2:2888:3888\n\
server.3=your_zookeeper_node_3:2888:3888\n\
'''

f = open('settings.json')

data = json.load(f)
for count, i in enumerate(data['Nodes']): 
    ansemble_config_data = ansemble_config_data.replace('your_zookeeper_node_{}'.format(count + 1), i['remote_host'])


for count,i in enumerate(data['Nodes']): 
    channel = Channel(hostname=i['remote_host'], username=i['remote_username'],
			password=i['remote_password'], pkey=sundry.get_pkey(i["remote_pkey_path"]), timeout=_timeout)

    channel.run("mkdir /opt/")
    channel.run("wget https://downloads.apache.org/zookeeper/zookeeper-3.6.2/apache-zookeeper-3.6.2-bin.tar.gz -P /opt/")
    #channel.run("cd && cd /opt/")
    channel.run("cd && cd /opt/ && tar xf apache-zookeeper-3.6.2-bin.tar.gz")
    channel.run("cd && cd /opt/ && ln -s apache-zookeeper-3.6.2-bin zookeeper")
    channel.run("cd && cd /opt/ && rm apache-zookeeper-3.6.2-bin.tar.gz")
    channel.run("echo " + "'{}'".format(ansemble_config_data) + " > " + "/opt/zookeeper/conf/zoo.cfg")
   
    channel.run("rm -rf /data/zookeeper/ ")
    channel.run("mkdir -p /data/zookeeper")
    channel.run("echo {} > /data/zookeeper/myid".format(count + 1))
f.close() 

#TODO run the daemon_director_ensemble