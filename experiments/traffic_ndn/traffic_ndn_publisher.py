
#imports da peca
import subprocess
from time import sleep
import sys
import argparse
import logging
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_LOG_LEVEL = logging.INFO 

from daemon import Daemon


class NDN_Publisher(Daemon):

    def run(self):
        cmd = "sudo nfd -c nfd.conf&"
        print("cmd: {}".format(cmd))
        subprocess.run([cmd], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sleep(5)

        cmd = "ndn-traffic-server /icn/ndn-traffic-server.conf"
        subprocess.run(cmd.split(' '), shell=False)#, stdout=super.so, stderr=super.se)
        # file_out = open('ndn-traffic-server.out', 'w')
        # file_err = open('ndn-traffic-server.err', 'w')
        # subprocess.run([cmd], shell=True, stdout=file_out, stderr=file_err)


def main():
    # arguments
    parser = argparse.ArgumentParser(description='Daemon NDN Publisher')

    help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
    parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

    cmd_choices = ['start', 'stop', 'restart', 'status']
    parser.add_argument('cmd', choices=cmd_choices)

    # read arguments from the command line
    args = parser.parse_args()

    # setup the logging facility
    if args.log == logging.DEBUG:
        logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                            datefmt=TIME_FORMAT, level=args.log)

    else:
        logging.basicConfig(format='%(asctime)s %(message)s',
                            datefmt=TIME_FORMAT, level=args.log)
    # shows input parameters
    logging.info("")
    logging.info("INPUT")
    logging.info("---------------------")
    logging.info("\t logging level : %s" % args.log)
    logging.info("\t command option: %s" % args.cmd)
    logging.info("")

    pid_file = "/tmp/daemon_ndn_publisher.pid"
    stdout   = "/tmp/daemon_ndn_publisher.stdout"
    stderr   = "/tmp/daemon_ndn_publisher.stderr"  

    logging.info("FILES")
    logging.info("---------------------")
    logging.info("\t pid_file      : %s" % pid_file)
    logging.info("\t stdout        : %s" % stdout)
    logging.info("\t stderr        : %s" % stderr)
    logging.info("")

    ndn_publisher = NDN_Publisher(pidfile=pid_file, stdout=stdout, stderr=stderr)

    # process input parameters
    if args.cmd == 'start':
        logging.info("Starting ndn_publisher")
        ndn_publisher.start()

    elif args.cmd == 'stop':
        logging.info("Stopping ndn_publisher")
        ndn_publisher.stop()

    elif args.cmd == 'restart':
        logging.info("Restarting ndn_publisher")
        ndn_publisher.restart()

    elif args.cmd == 'status':
        director_ensemble_pid = ndn_publisher.getpid()

        if not director_ensemble_pid:
            logging.info("ndn_publisher isn't running")
        else:
            logging.info("ndn_publisher is running [PID=%d]" % (ndn_publisher.getpid()))


if __name__ == '__main__':
    sys.exit(main())