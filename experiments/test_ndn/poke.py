import subprocess
import time
import sys

subprocess.run(["nfd-start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)
subprocess.run(["nfdc", "face", "create", "udp://"+sys.argv[1]])
time.sleep(5)
subprocess.run(["nfdc", "route", "add", "/demo/hello", "udp://"+sys.argv[1]])

for _ in range(0,10):
    time.sleep(0.5)
    subprocess.run(["ndnpeek", "-p", "/demo/hello"])
subprocess.run(["nfd-stop"])