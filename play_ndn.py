#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

try:

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
    from datetime import datetime
    from tqdm import tqdm
    

except ImportError as error:
	print(error)
	print()
	print("1. (optional) Setup a virtual environment: ")
	print("  python3 -m venv ~/Python3venv/icnstage ")
	print("  source ~/Python3venv/icnstage/bin/activate ")
	print()
	print("2. Install requirements:")
	print("  pip3 install --upgrade pip")
	print("  pip3 install -r requirements.txt ")
	print()
	sys.exit(-1)

import setup_kubernetes

LOG_LEVEL = logging.DEBUG
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_SLEEP_SECONDS = 5
STEP_TIME_SECS = 60

ZK_VERSION="zookeeper-3.8.0"
DEFAULT_QTY_DIRECTORS = 1
DEFAULT_QTY_ACTORS = 1
NODES_JSON_FILE = "nodes.json"

class Experiment():
    def __init__(self, directors, actors, fails_actors, fails_directors, name):
        self.directors = directors
        self.actors = actors
        self.fails_actors = fails_actors
        self.fails_directors = fails_directors
        self.name = name

    def __str__(self):
        return "Directors: {}   Actos: {}   Fails directors: {}   Fails actors: {}   Name: {}".format(
            self.directors, self.actors, self.fails_directors, self.fails_actors, self.name)


def find_node(kind, nodes, filter):
    logging.info("Finding pod {}, qty {}".format(kind, nodes))
    pod_found = None
    for i in range(1, nodes + 1):
        pod = "{}{}".format(kind, i)
        logging.info("\t pod: {}".format(pod))
        cmd = "ps aux | grep {}".format(filter)
        result = setup_kubernetes.run_cmd_kubernete_get_output(pod, cmd)
        if "/bin/bash" in result:
            logging.info("Pod found! {}".format(pod))
            pod_found = pod
            break
        else:
            logging.info("Pod not found! {}".format(pod))

    return pod_found


def find_leader_director(directors):
    logging.info("Finding leader director, qty {}".format(directors))
    pod_director = None
    for i in range(1, directors+1):
        pod = "director{}".format(i)
        logging.info("\t pod: {}".format(pod))
        cmd = "ps aux | grep daemon_directory.py"
        result = setup_kubernetes.run_cmd_kubernete_get_output(pod, cmd)
        if "/bin/bash" in result:
            logging.debug("Director found! {}".format(pod))
            pod_director = pod
            break
        else:
            logging.debug("Director not found! {}".format(pod))
            
    return pod_director

def find_running_actor(actors):
    filter = "ndn-traffic-client"
    return  find_node(nodes=actors, kind='actor', filter=filter)

def tqdm_sleep(secs):
    for i in tqdm(range(int(secs)), "Waiting max. {} secs.".format(secs)):
        sleep(1)


def main():
    # arguments
    parser = argparse.ArgumentParser(description='ICN Stage - Play TCP')

    help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
    parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

    mode_choices = ['local', 'fibre', 'edgenet']  # the first option is the default
    help_msg = "mode {}".format(mode_choices)
    parser.add_argument("--mode", "-m", help=help_msg, choices=mode_choices, default=mode_choices[0], type=str)

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
    setup_kubernetes.header(" PLAY NDN")

    try_name = datetime.now().strftime(TIME_FORMAT).replace(':', '-').replace(',', '_')
    results_dir = "results/play_ndn_{}".format(try_name)
    cmd = "mkdir -p {}".format(results_dir)
    setup_kubernetes.run_cmd(cmd)
    
    logging.info("")
    logging.info("INPUT")
    logging.info("---------------------")
    logging.info("\t logging level : {}".format(args.log))
    logging.info("\t mode option   : {}".format(args.mode))
    logging.info("\t try name      : {}".format(try_name))
    logging.info("\t results_dir   : {}".format(results_dir))
    logging.info("")

    experiments = []
    #1. benchmark: sem falha
    experiments += [Experiment(actors=1, directors=1, fails_actors=9, fails_directors=0, name="ndn_traffic_Peça_sem_falha")]

    # #2. problema 1: com falha de ator, sem backup
    experiments += [Experiment(actors=1, directors=1, fails_actors=1, fails_directors=0,
                               name="ndn_traffic_Peça_com_falha")]

    #
    # #3. solução 1: com falha de ator, com backup
    experiments += [Experiment(actors=2, directors=1, fails_actors=1, fails_directors=0,
                               name="ndn_traffic_Peça_com_falha_e_recuperação")]
    
    #
    # #4. problema 2: com falha de ator e diretor, sem backup de diretor (e backup de ator)
    # experiments += [Experiment(actors=2, directors=1, fails_actors=1, fails_directors=1)]
    #
    # #5. problema 2: com falha de ator e diretor, com backup de diretor (e backup de ator)
    # experiments += [Experiment(actors=2, directors=3, fails_actors=1, fails_directors=1)]
    plot_files = ""
    cmd = "kubectl delete pod --all"
    setup_kubernetes.run_cmd(cmd)
    for e in experiments:
        setup_kubernetes.header("Experiment: {}".format(e))
         

        cmd = "python3 setup_kubernetes.py --actors {} --directors {} --log {}".format(e.actors, e.directors, args.log)
        setup_kubernetes.run_cmd(cmd)
        
        k8s_cmd = "icn-stage/cli.py addactors".format(args.log)
        setup_kubernetes.run_cmd_kubernete("director1", k8s_cmd)

        director_leader = "director1"
        if e.directors > 1:
            director_leader = find_leader_director(e.directors)

        k8s_cmd = "python3 icn-stage/cli.py traffic".format(args.log)
        setup_kubernetes.run_cmd_kubernete("director1", k8s_cmd)

        running_actor = "actor1"
        if e.actors > 1:
            running_actor = find_running_actor(e.actors)

        datetime_begin = datetime.now()
        logging.info("")
        tqdm_sleep(STEP_TIME_SECS)
        #wait 60 secs
        #fail director if need
        if e.fails_directors > 0:
            cmd = "kubectl delete pod {}".format(director_leader)
            setup_kubernetes.run_cmd(cmd)
            logging.info("\t fail directors done {}".format(director_leader))
        else:
            logging.info("\t Skipping fail director")

        tqdm_sleep(STEP_TIME_SECS)
        #fail actor if need
        if e.fails_actors > 0:
            cmd = "kubectl delete pod {}".format(running_actor)
            setup_kubernetes.run_cmd(cmd)
            logging.info("\t fail actor done {}".format(running_actor))
        else:
            logging.info("\t Skipping fail actor")

        tqdm_sleep(STEP_TIME_SECS)
        logging.info("\t Experiment finished {}".format(e.name))

        result_file = "{}/{}.txt".format(results_dir, e.name)

        cmd = "kubectl cp publisher1:/tmp/daemon_ndn_publisher.stdout {}".format(result_file)
        setup_kubernetes.run_cmd(cmd)
        logging.info("\t Result: {}".format(result_file))
        tqdm_sleep(10)
        #wait 60 sec
        #finish
        # cmd = "mv /tmp/daemon_ndn_publisher.stdout /tmp/daemon_ndn_publisher.stdout_{}".format(e.name)
        # setup_kubernetes.run_cmd_kubernete(cmd)

        plot_files += " {}".format(result_file)
        cmd = "kubectl delete pod --all"
        setup_kubernetes.run_cmd(cmd)

        choosen_actor = ""

    cmd = "python3 plot/plot.py -o results_dir/{} {}".format(results_dir, try_name)
    setup_kubernetes.run_cmd(cmd)

if __name__ == '__main__':
    sys.exit(main())