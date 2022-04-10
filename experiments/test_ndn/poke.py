import subprocess
import time
import sys

sys.stdout = open("ndnpeek_output.txt", "w")

subprocess.run(["nfd-start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)
subprocess.run(["nfdc", "face", "create", "udp://"+sys.argv[1]])
time.sleep(5)
subprocess.run(["nfdc", "route", "add", "/demo/hello", "udp://"+sys.argv[1]])

for _ in range(0,10):
    time.sleep(0.5)
    peek_out = subprocess.run(["ndnpeek", "-p", "/demo/hello"], stdout=subprocess.PIPE)
    print(peek_out.stdout)
subprocess.run(["nfd-stop"])

sys.stdout.close()