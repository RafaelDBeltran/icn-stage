#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

import argparse
import logging
import os
import sys
import subprocess
import threading
from time import sleep
import time
import subprocess
from functools import partial
import shlex
from datetime import datetime, timedelta
from tqdm import tqdm
from math import ceil

TIME_FORMAT = '%Y-%m-%d_%H:%M:%S'
DEFAULT_DURATION_SECS = 180
DEFAULT_INTERVAL_MILLISENCONDS = 100

def prepare(publisher):
    publisher = "udp://{}".format(publisher)
    data_name = "/example/"

    subprocess.run(["sudo nfd -c nfd.conf&"], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sleep(5)

    cmd = "nfdc face create {}".format(publisher)
    print("cmd: {}".format(cmd))
    subprocess.run(shlex.split(cmd))
    sleep(5)

    cmd = "nfdc route add {} {}".format(data_name, publisher)
    print("cmd: {}".format(cmd))
    subprocess.run(shlex.split(cmd))


def act(duration_secs=DEFAULT_DURATION_SECS, interval_millisecs=DEFAULT_INTERVAL_MILLISENCONDS):
    # '''
    # -h [ --help ]                 print this help message and exit
    # -c [ --count ] arg            total number of Interests to be generated
    # -i [ --interval ] arg (=1000) Interest generation interval in milliseconds
    # -q [ --quiet ]                turn off logging of Interest generation/Data reception
    # interval: 1000 / (16packets * 8Kbytes) = 1Mbits/second ~ 63milliseconds
    # '''
    count = duration_secs * ceil(1000/interval_millisecs)
    cmd = "ndn-traffic-client "
    cmd += " -c {}".format(count)
    cmd += " -i {}".format(interval_millisecs)
    cmd += " ndn-traffic-client.conf >> ndn_traffic_receiver_output.txt"
    print("cmd: {}".format(cmd))
    subprocess.run([cmd], shell=True)

def main():
    # arguments
    parser = argparse.ArgumentParser(description='Daemon NDN Publisher')

    help_msg = "logging level (INFO={} DEBUG={})".format(logging.INFO, logging.DEBUG)
    parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

    help_msg = "start time (Y-m-d_H:M:S)"
    parser.add_argument("--start", "-s", help=help_msg, default=None, type=str)

    help_msg = "duration secs (default={})".format(DEFAULT_DURATION_SECS)
    parser.add_argument("--duration", "-d", help=help_msg, default=DEFAULT_DURATION_SECS, type=int)

    help_msg = "interval milliseconds (default={})".format(DEFAULT_INTERVAL_MILLISENCONDS)
    parser.add_argument("--interval", "-i", help=help_msg, default=DEFAULT_INTERVAL_MILLISENCONDS, type=int)

    help_msg = "publisher (IPv4)"
    parser.add_argument("--publisher", "-p", help=help_msg, default=None, type=str, required=True)



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
    logging.info("---------------------------------")
    logging.info("\t logging level    : {}".format(args.log))
    logging.info("\t start time       : {}".format(args.start))
    logging.info("\t plan. dur. (secs): {}".format(args.duration))

    logging.info("")

    prepare(args.publisher)

    start_time = datetime.now()
    start_time = start_time.replace(second=0, microsecond=0)
    start_time += timedelta(seconds=60)
    if args.start is not None:
        start_time = datetime.strptime(args.start, TIME_FORMAT)

    finish_time = start_time + timedelta(seconds=args.duration)

    now = datetime.now().replace(microsecond=0)
    duration = (finish_time - now)
    wait = (start_time - now)

    logging.info("")
    logging.info("CALCULATED")
    logging.info("---------------------------------")
    logging.info("\t start time       : {}".format(start_time))
    logging.info("\t finish time      : {}".format(finish_time))
    logging.info("\t now              : {}".format(now))
    logging.info("\t real dur.        : {}".format(duration))
    logging.info("\t real dur. (secs) : {}".format(duration.seconds))
    logging.info("\t wait             : {}".format(wait))
    logging.info("\t wait      (secs) : {}".format(wait.seconds))
    # logging.info("")

    if now > finish_time:
        logging.error("ERROR: {} > {}".format(now, finish_time))
        sys.exit(-1)

    duration_secs = args.duration
    if now < start_time:
        logging.info("sleeping {} seconds".format(wait.seconds))
        sleep(wait.seconds)
    else:
        duration = (finish_time - now)
        duration_secs = duration.seconds

    logging.info("\t duration_secs   : {}".format(duration_secs))
    logging.info("")

    act(duration_secs=duration_secs, interval_millisecs=args.interval)


if __name__ == '__main__':
    sys.exit(main())