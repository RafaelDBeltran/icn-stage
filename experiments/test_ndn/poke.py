import subprocess
import time
import sys

#sys.stdout = open("ndnpeek_output.txt", "w")

subprocess.run(["sudo nfd&"],shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)
subprocess.run(["nfdc", "face", "create", "udp://"+sys.argv[1]])
time.sleep(5)
data_name = sys.argv[2]
subprocess.run(["nfdc", "route", "add", data_name, "udp://"+sys.argv[1]])

for i in range(10):
    time.sleep(0.5)
    cmd = "ndnpeek -p {}".format(data_name)
    # print(cmd)
    # peek_out = subprocess.run(cmd.split(" "), stdout=subprocess.PIPE)
    # print(peek_out.stdout)
    print("run {}: cmd: {}".format(i, cmd))
    subprocess.run(cmd.split(" "))

# subprocess.run(["nfd-stop"])

#sys.stdout.close()