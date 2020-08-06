import subprocess
import time
import sys

time.sleep(10)

subprocess.run(["nfdc", "face", "create", "udp://"+sys.argv[1]])

time.sleep(5)

subprocess.run(["nfdc", "route", "add", "/example/", "udp://"+sys.argv[1]])

time.sleep(10)
try:
    subprocess.run(["ndn-traffic-client -q -c 20 ndn-traffic-client.conf >> ndn_traffic_output.txt"],shell = True)
finally:
    subprocess.run(["sudo nfd-stop"], shell = True)
