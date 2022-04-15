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

TIME_FORMAT = '%Y-%m-%d_%H:%M:%S'
DEFAULT_KBYTES = 8
DEFAULT_QTY = 100

def main():
    # arguments
    parser = argparse.ArgumentParser(description='Daemon NDN Publisher')

    help_msg = "logging level (INFO={} DEBUG={})".format(logging.INFO, logging.DEBUG)
    parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

    help_msg = "kbytes"
    parser.add_argument("--kbytes", "-k", help=help_msg, default=DEFAULT_KBYTES, type=int)

    help_msg = "Quantity (1..100) must be divisible by 100"
    parser.add_argument("--qty", "-q", help=help_msg, default=DEFAULT_QTY, type=int)


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
    logging.info("\t logging level      : {}".format(args.log))
    logging.info("\t Kbytes             : {}".format(args.kbytes))
    logging.info("\t quantity           : {}".format(args.qty))
    logging.info("")

    if 100 % args.qty != 0:
        logging.error("ERROR: 100 % qty != 0")
        sys.exit(-1)

    # sys.exit(main())
    f_server = open("ndn-traffic-server.conf", 'w')
    f_client = open("ndn-traffic-client.conf", 'w')
    content = "a" * args.kbytes * 1000
    percentage = 100 /args.qty
    for i in range(args.qty):
        name = "/example/8KB{}".format(i + 1)

        config = '''##########
Name={}
Content={}
'''.format(name, content)
        f_server.write(config)

        config = '''##########
TrafficPercentage={}
Name={}
ExpectedContent={}
'''.format(percentage, name, content)
        f_client.write(config)

    f_client.close()
    f_server.close()
    print("Done!")


if __name__ == '__main__':
    sys.exit(main())