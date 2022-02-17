#imports do controle baseado em NTP
from asyncio import sleep
import ntplib
from datetime import datetime, timezone
from time import sleep
import threading
#imports da peca
import subprocess
import time
import sys

# Start_time = datetime.strptime(sys.argv[2],'%d-%m-%y %H:%M:%S')
# Finish_time = datetime.strptime(sys.argv[3],'%d-%m-%y %H:%M:%S')

Start_time = datetime.strptime('16-02-22 20:42:00','%d-%m-%y %H:%M:%S')
Finish_time = datetime.strptime('16-02-22 20:45:00','%d-%m-%y %H:%M:%S')

c = ntplib.NTPClient()
# Provide the respective ntp server ip in below function

def get_current_time():

    response = c.request('0.br.pool.ntp.org', version=3)
    response.offset
    
    time_from_ntp = datetime.fromtimestamp(response.tx_time).strftime('%d-%m-%y %H:%M:%S')
    return datetime.strptime(time_from_ntp,'%d-%m-%y %H:%M:%S')

def peca():

    subprocess.run(["sudo nfd-stop"],shell = True)
    subprocess.run(["sudo cp low.conf /usr/local/etc/mini-ndn/"],shell = True)

    subprocess.run(["sudo nfd -c /usr/local/etc/mini-ndn/low.conf > /dev/null &"],shell = True  ,stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
    subprocess.run(["nfdc", "face", "create", "udp://"+sys.argv[1]])
    subprocess.run(["nfdc", "route", "add", "/example/", "udp://"+sys.argv[1]])

    '''
    -h [ --help ]                 print this help message and exit
    -c [ --count ] arg            total number of Interests to be generated
    -i [ --interval ] arg (=1000) Interest generation interval in milliseconds
    -q [ --quiet ]                turn off logging of Interest generation/Data reception
    interval: 1000 / (16packets * 8Kbytes) = 1Mbits/second ~ 63milliseconds 
    '''
    try:
        subprocess.run(["ndn-traffic-client -c 100 -i 100 ndn-traffic-client.conf >> /home/vagrant/ndn_traffic_client_output.txt"],shell = True)
    finally:
        subprocess.run(["sudo nfd-stop"], shell = True)

def stop_play():

    print('Thread Iniciada {}'.format(get_current_time()))
    while ((get_current_time() < Finish_time)):
        
        peca()

        # sleep(5)
    print('Peca Finalizada')

time_from_ntp = get_current_time()

Seconds_to_start = ((Start_time - time_from_ntp).total_seconds())

if Seconds_to_start > 0:
    print('Começando Peça')
    sleep(Seconds_to_start)
    play_thread = threading.Thread(target=stop_play, args=())
    play_thread.start()
elif get_current_time() < Finish_time:
    print('Voltando a Peça')
    play_thread = threading.Thread(target=stop_play, args=())
    play_thread.start()
else:
    print('Peca já encerrada')

