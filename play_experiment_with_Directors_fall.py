from time import sleep
import sys
from Remote_ICN_stage import RemoteControllICN_stage
import time
import subprocess
import threading
import json



def callPlayDirector():
    subprocess.run('python3 playDirector.py &',shell=True)

Pecas = ['Peça_sem_falha']


for peca in Pecas:

    print('######## Ligando Vagrant ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))

    subprocess.run('vagrant up', shell=True)

    instancia = RemoteControllICN_stage()

    try:
        CONFIG_FILE = "config.json"
        JSON_FILE = json.load(open(CONFIG_FILE))

        for count, i in enumerate(JSON_FILE['auxiliars']):
            remote_host = i['remote_hostname']
            break
        
        print('######## Excluir log antigo do Auxiliar ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
        instancia.send_command_with_parameters('sudo rm /home/vagrant/log.out', i['remote_hostname'], i['remote_username'], i['remote_password'], '.vagrant/machines/{}/virtualbox/private_key'.format(i['Function']))
    except:
        print('Erro ao excluir log antigo remoto')
    
    sleep(60)

    print('######## Iniciando Ensemble ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    instancia.send_command('ensemble-start')

    print('######## Iniciando Daemon Director ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    instancia.send_command('start')

    print('######## Rodando Reset ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    instancia.send_command('reset')

    print('######## Reiniciando Tasks ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    instancia.send_command('reset-tasks')

    print('######## Adicionando atores ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    instancia.send_command('addactors')

    print('######## Iniciando NDN Traffic Generator ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    # instancia.send_command('traffic' +' '+ '17-02-22 00:38:00' +' '+ '17-02-22 00:45:00')
    instancia.send_command('traffic')
    
    #sleep(30)

    while True:
        Resultado = instancia.get_busy_actor()
        print('######## GetBusyActor: {} ######## {}'.format(Resultado, time.strftime("%H:%M:%S", time.localtime())))
        # print('O resultado eh do tipo ' + str(type(Resultado))+ ' : ' +str(Resultado) + ':' +type(Resultado))

        if type(Resultado) == str:
            break
        sleep(30)

    print('saiu do loop {}'.format(Resultado))

    x = threading.Thread(target= callPlayDirector, args=())
    x.start()

    print('######## Iniciando Espera do fim do processo ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))

    try:
        instancia.send_command_to_busy_actor('tail --pid=$(pgrep -f traffic_client.py) -f /dev/null', Resultado)
    except:
        print('Erro no monitoramento do processo')
   
    print('######## Processo acabou ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    print('Rodar Get Results')

    try:
        CONFIG_FILE = "config.json"
        JSON_FILE = json.load(open(CONFIG_FILE))

        for count, i in enumerate(JSON_FILE['auxiliars']):
            remote_host = i['remote_hostname']
            break

        instancia.copyfile(remote_host)
    except:
        print('Erro ao copiar log remoto')

    subprocess.run('mv log.out ndn_traffic_{}.txt'.format(peca), shell=True)

    sleep(10)

    try:
        print('######## Desligando Vagrant ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
        #subprocess.run('vagrant halt', shell=True)
    except:
        print('Erro ao desligar vagrant')

subprocess.run('vagrant halt Director1 Director2 Director3', shell=True)
