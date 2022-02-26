#imports do controle baseado em NTP
from asyncio import sleep
import ntplib
from datetime import datetime, timezone, timedelta
from time import sleep
import threading
#imports da peca
import subprocess
import time
import sys

# Start_time = datetime.strptime(sys.argv[2],'%d-%m-%y %H:%M:%S')
# Finish_time = datetime.strptime(sys.argv[3],'%d-%m-%y %H:%M:%S')

now = datetime.now()

print("now =", now)

DATETIME_FORMAT = '%d-%m-%y %H:%M:%S'
dt_string = now.strftime(DATETIME_FORMAT)

#Start_time = datetime.strptime('23-02-22 09:35:00',DATETIME_FORMAT)
Start_time = now
Start_time = Start_time + timedelta(minutes=5)
#print(Start_time)
#Finish_time = datetime.strptime('23-02-22 08:42:00','%d-%m-%y %H:%M:%S')
Finish_time = Start_time + timedelta(minutes=15)

# Start_time = datetime.strptime('16-02-22 20:42:00','%d-%m-%y %H:%M:%S')
# Finish_time = datetime.strptime('16-02-22 20:45:00','%d-%m-%y %H:%M:%S')

c = ntplib.NTPClient()
# Provide the respective ntp server ip in below function

def get_current_time():

    NTPcontrol = False
    var_time = None
    while True:
        try:
            c = ntplib.NTPClient()

            response = c.request('0.br.pool.ntp.org', version=3)
            response.offset

            time_from_ntp = datetime.fromtimestamp(response.tx_time).strftime(DATETIME_FORMAT)
            var_time = datetime.strptime(time_from_ntp,DATETIME_FORMAT)
            NTPcontrol = True
        except ntplib.NTPException as e:
            print('NTP client request error: {}'.format(str(e)))

        if NTPcontrol == True:
            break

    return var_time

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

