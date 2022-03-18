from time import sleep
import sys
from Remote_ICN_stage import RemoteControllICN_stage
import time
import subprocess
import threading
import json
import logging

LOG_LEVEL = logging.INFO
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
CONFIG_FILE = "config.json"

if LOG_LEVEL == logging.DEBUG:
    logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')
else:
    logging.basicConfig(format='%(asctime)s %(message)s',
                datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')


# Pecas = ['Peça_sem_falha','Peça_com_falha','Peça_com_falha/recuperacao']
# Pecas = ['Peça_sem_falha','Peça_com_falha/recuperacao']
# Pecas = ['Peça_com_falha']
# Pecas = ['Peça_sem_falha']
Pecas = ['Peça_com_falha/recuperacao']

for peca in Pecas:

    logging.info('######## Ligando Vagrant ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))

    subprocess.run('vagrant up', shell=True)

    instancia = RemoteControllICN_stage()

    try:        
        JSON_FILE = json.load(open(CONFIG_FILE))

        for count, i in enumerate(JSON_FILE['auxiliars']):
            remote_host = i['remote_hostname']
            break
        
        logging.info('######## Excluir log antigo do Auxiliar ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
        instancia.send_command_with_parameters('sudo rm /home/vagrant/log.out', i['remote_hostname'], i['remote_username'], i['remote_password'], '.vagrant/machines/{}/virtualbox/private_key'.format(i['Function']))
    except:
        logging.debug('Erro ao excluir log antigo remoto')
    
    sleep(60)

    logging.info('######## Iniciando Ensemble ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    instancia.send_command('ensemble-start')

    logging.info('######## Iniciando Daemon Director ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    instancia.send_command('start')

    logging.info('######## Rodando Reset ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    instancia.send_command('reset')

    logging.info('######## Reiniciando Tasks ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    instancia.send_command('reset-tasks')

    logging.info('######## Adicionando atores ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    instancia.send_command('addactors')

    logging.info('######## Iniciando NDN Traffic Generator ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))

    instancia.send_command('traffic')

    while True:
        try:
            Resultado = instancia.get_busy_actor()
            logging.info('######## GetBusyActor: {} ######## {}'.format(Resultado, time.strftime("%H:%M:%S", time.localtime())))
            # print('O resultado eh do tipo ' + str(type(Resultado))+ ' : ' +str(Resultado) + ':' +type(Resultado))

            if type(Resultado) == str:
                break
            sleep(30)
        except:
            logging.debug('Erro ao obter o resultado do busy actor')
            
    logging.info('saiu do loop {}'.format(Resultado))

    logging.info('######## Iniciando Espera do fim do processo ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))

    if peca == 'Peça_com_falha' or peca == 'Peça_com_falha/recuperacao':
        try:
            x = threading.Thread(target= instancia.send_command_to_busy_actor, args=('sleep 5m && sudo shutdown now',Resultado,))
            x.start()
        except:
            logging.info('Error: unable to start thread')

    try:
        instancia.send_command_to_busy_actor('tail --pid=$(pgrep -f traffic_client.py) -f /dev/null', Resultado)
    except:
        logging.debug('Erro no monitoramento do processo')
    
    if peca == 'Peça_com_falha/recuperacao':
        sleep(250)

        JSON_FILE = json.load(open(CONFIG_FILE))
        
        for count, i in enumerate(JSON_FILE['workers']):
            if i['remote_hostname'] == Resultado:
                pass
            else:
                try:
                    instancia.send_command_to_busy_actor('tail --pid=$(pgrep -f traffic_client.py) -f /dev/null', i)
                    instancia.copyfile(i)
                except:
                    logging.debug('Erro na segunda tentativa de buscar novo ator')
    
    elif peca == 'Peça_com_falha':
        JSON_FILE = json.load(open(CONFIG_FILE))
        
        for count, i in enumerate(JSON_FILE['workers']):
            try:
                logging.info('Desligando Ator {}'.format(i['remote_hostname']))
                instancia.send_command_with_parameters('sudo shutdown now &', i['remote_hostname'], i['remote_username'], i['remote_password'], '.vagrant/machines/{}/virtualbox/private_key'.format(i['Function']))
            except:
                logging.debug('Erro na tentativa de desligar os Atores: {}'.format(i['remote_hostname']))
        
        for count, i in enumerate(JSON_FILE['Nodes']):
            try:
                logging.info('Desligando Diretor {}'.format(i['remote_hostname']))
                instancia.send_command_with_parameters('sudo shutdown now &', i['remote_hostname'], i['remote_username'], i['remote_password'], '.vagrant/machines/{}/virtualbox/private_key'.format(i['Function']))
            except:
                logging.debug('Erro na tentativa de desligar os Diretores: {}'.format(i['remote_hostname']))

    logging.info('######## Processo acabou ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
    logging.info('Rodar Get Results')

    try:
        JSON_FILE = json.load(open(CONFIG_FILE))

        for count, i in enumerate(JSON_FILE['auxiliars']):
            remote_host = i['remote_hostname']
            break

        instancia.copyfile(remote_host)
    except:
        logging.debug('Erro ao copiar log remoto')

    subprocess.run('mv log.out ndn_traffic_{}.txt'.format(peca), shell=True)

    sleep(10)

    try:
        logging.info('######## Desligando Vagrant ######## {}'.format(time.strftime("%H:%M:%S", time.localtime())))
        subprocess.run('vagrant halt', shell=True)
    except:
        logging.debug('Erro ao desligar vagrant')

