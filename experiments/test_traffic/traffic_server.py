import logging
import subprocess
import time


class NDN_traffic:


    def traffic_start(self, Log_out = '/home/vagrant/ndn_out.log', Log_error = '/home/vagrant/ndn_error.log'):

        subprocess.run(["sudo nfd-stop"], shell=True, stderr=subprocess.DEVNULL)
        subprocess.run(["sudo cp /home/vagrant/low.conf /usr/local/etc/mini-ndn/"],shell = True  ,stdout = Log_out, stderr = Log_error)
        subprocess.run(["sudo nfd -c /usr/local/etc/ndn/low.conf &> /dev/null &"],shell = True  ,stdout = Log_out, stderr = Log_error)

        time.sleep(2)

        print("Starting NDN Traffic Client")
        try:
            subprocess.run(["sudo ndn-traffic-server /home/vagrant/ndn-traffic-server.conf"], shell=True,  stderr = Log_error)
            logging.info("Waiting... ")

        except:
            print("Finalized by actor")


def call_ndn_traffic():
    instance_ndn_traffic = NDN_traffic()
    instance_ndn_traffic.traffic_start()