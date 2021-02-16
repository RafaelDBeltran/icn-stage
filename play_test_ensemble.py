import argparse
import logging
import os
import sys
import threading
import time
import subprocess
import shlex

from functools import partial
from time import sleep
from tqdm import trange

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_LOG_LEVEL = logging.INFO

def main():

    parser = argparse.ArgumentParser(description='*** Play test ensemble ***')
    help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
    parser.add_argument("--log", "-l", help=help_msg, default=DEFAULT_LOG_LEVEL, type=int)
    args = parser.parse_args()

    if args.log == logging.DEBUG:
        
        logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
                            datefmt=TIME_FORMAT, level=args.log)
    else:
    
        logging.basicConfig(format='%(asctime)s %(message)s',
                            datefmt=TIME_FORMAT, level=args.log)

    logging.info("")
    logging.info("SETTINGS")
    logging.info("---------------------")
    logging.info("\t Logging level : {}".format(args.log))
    logging.info("\n")

    logging.info('******************1*******************\n Instalando diretores remotos')
    os.system('python3 director_manager.py install')

    logging.info('******************2*******************\n Rodando diretores remotos')
    os.system('python3 director_manager.py run')



if __name__ == '__main__':
    sys.exit(main())
