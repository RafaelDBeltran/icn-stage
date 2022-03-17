from time import sleep
import sys
from Remote_ICN_stage import RemoteControllICN_stage
import time
import subprocess
import threading
import json



print('######## Ligando Vagrant ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))

# subprocess.run('vagrant up Director1', shell=True)
# subprocess.run('vagrant up Director2', shell=True)
# subprocess.run('vagrant up Director3', shell=True)

instancia = RemoteControllICN_stage()

print('######## Iniciando Ensemble ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
instancia.send_command('ensemble-start')

print('######## Após 5min insere falha ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
sleep(300)
CONFIG_FILE = "config.json"
JSON_FILE = json.load(open(CONFIG_FILE))

for count, i in enumerate(JSON_FILE['Nodes']):
    try:            
        if instancia.detect_zookeeper_role(i['remote_hostname']) == True:
            print('######## Inserindo falha no Diretor {} ######## {}'.format(i['remote_hostname'], time.strftime("%H:%M:%S", time.localtime())))
            instancia.send_command_with_parameters('sudo shutdown now', i['remote_hostname'], i['remote_username'], i['remote_password'], '.vagrant/machines/{}/virtualbox/private_key'.format(i['Function']))
        else:
            pass
        
    except:
        print('Erro na tentativa de desligar os Diretores: {}'.format(i['remote_hostname']))

sleep(10)

try:
    print('######## Desligando Vagrant ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    subprocess.run('vagrant halt Director1', shell=True)
    subprocess.run('vagrant halt Director2', shell=True)
    subprocess.run('vagrant halt Director3', shell=True)
except:
    print('Erro ao desligar vagrant')

