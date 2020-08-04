import subprocess
import time
import sys

sys.stdout = open("ndn_traffic_output.txt", "w")

subprocess.run(["nfd-start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(10)
subprocess.run(["nfdc", "face", "create", "udp://"+sys.argv[1]])

time.sleep(5)
subprocess.run(["nfdc", "route", "add", "/example/", "udp://"+sys.argv[1]])

time.sleep(10)

traffic_output = subprocess.run(["ndn-traffic-client", "-c", "2048", "-i", "1000", "ndn-traffic-client.conf"], stdout=subprocess.PIPE)
print(traffic_output.stdout)

subprocess.run(["nfd-stop"])

sys.stdout.close()