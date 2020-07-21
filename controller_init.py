#
#	@author: Nelson Antonio Antunes Junior
#	@email: nelson.a.antunes at gmail.com
#	@date: (DD/MM/YYYY) 24/01/2017

import sys, os, subprocess

try:
    import kazoo, paramiko, scp

except ImportError as error:
    print(error)
    print()
    print("1. Setup a virtual environment: ")
    print("  python3 - m venv ~/Python3env/ExtendedEasyExp ")
    print("  source ~/Python3env/ExtendedEasyExp/bin/activate ")
    print()
    print("2. Install requirements:")
    print("  pip3 install --upgrade pip")
    print("  pip3 install -r requirements.txt ")

    print()
    sys.exit(-1)


from modules.conlib.controller_client import ControllerClient


def main():
    print("STARTING ZK")
    # subprocess.call("./zookeeper-3.4.9/bin/zkServer.sh start", shell=True)
    subprocess.call("./apache-zookeeper-3.6.1/bin/zkServer.sh start", shell=True)

    print("CONNECTING ZK")
    cclient = ControllerClient()

    print("CREATING BASIC ZNODES ZK")
    cclient.config_create_missing_paths()

    if not os.path.isdir("./experiments"):
        print("CREATING EXPERIMENTS FOLDER")
        os.mkdir("./experiments")

    subprocess.call("python3 daemon_controller.py restart", shell=True)

if __name__ == '__main__':
    sys.exit(main())
