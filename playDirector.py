from time import sleep
import sys
from Remote_ICN_stage import RemoteControllICN_stage
import time
import subprocess
import threading
import json

print('######## Ligando Vagrant ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))

instancia = RemoteControllICN_stage()

#print('######## Iniciando Ensemble ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
#instancia.send_command('ensemble-start')

print('######## Após 5min insere falha ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
sleep(150)
CONFIG_FILE = "config.json"
JSON_FILE = json.load(open(CONFIG_FILE))

DirectorDesligado = None

for count, i in enumerate(JSON_FILE['Nodes']):
    try:
        if instancia.detect_zookeeper_role(i['remote_hostname']) == True:
            DirectorDesligado = i['remote_hostname']
            print('######## Inserindo falha no Diretor {} ######## {}'.format(i['remote_hostname'], time.strftime("%H:%M:%S", time.localtime())))
            instancia.send_command_with_parameters('sudo shutdown now &', i['remote_hostname'], i['remote_username'], i['remote_password'], '.vagrant/machines/{}/virtualbox/private_key'.format(i['Function']))
            break
        else:
            pass
        
    except:
        print('Erro na tentativa de desligar os Diretores: {}'.format(i['remote_hostname']))

print('######## Diretor morto {} ######## {}'.format(DirectorDesligado, time.strftime("%H:%M:%S", time.localtime())))

sleep(60)

for count, i in enumerate(JSON_FILE['Nodes']):
    try:            
        if i['remote_hostname'] == DirectorDesligado:
            print('######## Ligando Diretor Derrubado {} ######## {}'.format(i['remote_hostname'], time.strftime("%H:%M:%S", time.localtime())))
            p = subprocess.run('vagrant up {}'.format(i['Function']), shell=True, capture_output=True)
            sleep(30)
            instancia.send_command_with_parameters('cd /home/vagrant/opt/zookeeper/bin && sudo bash zkServer.sh start &', i['remote_hostname'], i['remote_username'], i['remote_password'], '.vagrant/machines/{}/virtualbox/private_key'.format(i['Function']))
            sleep(20)
            instancia.send_command_with_parameters('cd /home/vagrant/icn-stage && sudo python3 daemon_ensemble.py --start &', i['remote_hostname'], i['remote_username'], i['remote_password'], '.vagrant/machines/{}/virtualbox/private_key'.format(i['Function']))


    except:
        print('Erro na tentativa de desligar os Diretores: {}'.format(i['remote_hostname']))

sleep(120)

for count, i in enumerate(JSON_FILE['Nodes']):
    try:            
        if instancia.detect_zookeeper_role(i['remote_hostname']) == True:
            DirectorDesligado = i['remote_hostname']
            print('######## Inserindo falha no Diretor {} ######## {}'.format(i['remote_hostname'], time.strftime("%H:%M:%S", time.localtime())))
            instancia.send_command_with_parameters('sudo shutdown now &', i['remote_hostname'], i['remote_username'], i['remote_password'], '.vagrant/machines/{}/virtualbox/private_key'.format(i['Function']))
            break
        else:
            pass
        
    except:
        print('Erro na tentativa de desligar os Diretores: {}'.format(i['remote_hostname']))

print('######## Diretor morto {} ######## {}'.format(DirectorDesligado, time.strftime("%H:%M:%S", time.localtime())))

sleep(60)

for count, i in enumerate(JSON_FILE['Nodes']):
    try:            
        if i['remote_hostname'] == DirectorDesligado:
            print('######## Ligando Diretor Derrubado {} ######## {}'.format(i['remote_hostname'], time.strftime("%H:%M:%S", time.localtime())))
            p = subprocess.run('vagrant up {}'.format(i['Function']), shell=True, capture_output=True)
            sleep(30)
            instancia.send_command_with_parameters('cd /home/vagrant/opt/zookeeper/bin && sudo bash zkServer.sh start &', i['remote_hostname'], i['remote_username'], i['remote_password'], '.vagrant/machines/{}/virtualbox/private_key'.format(i['Function']))
            sleep(20)
            instancia.send_command_with_parameters('cd /home/vagrant/icn-stage && sudo python3 daemon_ensemble.py --start &', i['remote_hostname'], i['remote_username'], i['remote_password'], '.vagrant/machines/{}/virtualbox/private_key'.format(i['Function']))

    except:
        print('Erro na tentativa de desligar os Diretores: {}'.format(i['remote_hostname']))

sleep(120)

#subprocess.run('vagrant halt Director1 Director2 Director3', shell=True)
