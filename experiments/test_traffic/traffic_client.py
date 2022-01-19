import subprocess
import time
import sys

time.sleep(10)
subprocess.run(["sudo cp low.conf /usr/local/etc/mini-ndn/"],shell = True)
time.sleep(2)
subprocess.run(["sudo nfd -c /usr/local/etc/mini-ndn/low.conf > /dev/null &"],shell = True  ,stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
subprocess.run(["nfdc", "face", "create", "udp://"+sys.argv[1]])
subprocess.run(["nfdc", "route", "add", "/example/", "udp://"+sys.argv[1]])

time.sleep(10)
'''
-h [ --help ]                 print this help message and exit
-c [ --count ] arg            total number of Interests to be generated
-i [ --interval ] arg (=1000) Interest generation interval in milliseconds
-q [ --quiet ]                turn off logging of Interest generation/Data reception
interval: 1000 / (16packets * 8Kbytes) = 1Mbits/second ~ 63milliseconds 
'''
try:
    subprocess.run(["ndn-traffic-client -c 6200 -i 100 ndn-traffic-client.conf >> ndn_traffic_client_output.txt"],shell = True)
finally:
    subprocess.run(["sudo nfd-stop"], shell = True)
