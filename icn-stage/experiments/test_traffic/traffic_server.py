import logging
import subprocess
import time


class NDN_traffic:


    def traffic_start(self):

        subprocess.run(["nfd-stop"], shell=True)
        #subprocess.run(["sudo cp /home/vagrant/low.conf /usr/local/etc/mini-ndn/"],shell = True )
        subprocess.run(["nfd -c low.conf &> /dev/null &"],shell = True)

        time.sleep(2)

        print("Starting NDN Traffic Server")
        try:
            subprocess.run(["ndn-traffic-server ndn-traffic-server.conf"], shell=True)
            logging.info("Waiting... ")

        except:
            print("Finalized by actor")


def call_ndn_traffic():
    instance_ndn_traffic = NDN_traffic()
    instance_ndn_traffic.traffic_start()

call_ndn_traffic()