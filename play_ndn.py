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
    from datetime import datetime, timedelta
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
TIME_FORMAT = '%Y-%m-%d_%H:%M:%S'
DEFAULT_SLEEP_SECONDS = 5
STEP_TIME_SECS = 60*3

ZK_VERSION="zookeeper-3.8.0"
DEFAULT_QTY_DIRECTORS = 1
DEFAULT_QTY_ACTORS = 1
NODES_JSON_FILE = "nodes.json"

DEFAULT_DURATION_SECS = STEP_TIME_SECS * 3
DEFAULT_INTERVAL_MILLISENCONDS = 100

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
        for line in result.split('\n'):
            logging.info("line: {}".format(line))
            if filter in line and 'grep' not in line:
                logging.info("Pod found! {}".format(pod))
                pod_found = pod
                return pod_found
            else:
                logging.info("Pod not found! {}".format(pod))

    return pod_found


# def find_leader_director(directors):
#     logging.info("Finding leader director, qty {}".format(directors))
#     pod_director = None
#     for i in range(1, directors+1):
#         pod = "director{}".format(i)
#         logging.info("\t pod: {}".format(pod))
#         cmd = "ps aux | grep daemon_directory.py"
#         result = setup_kubernetes.run_cmd_kubernete_get_output(pod, cmd)
#         if "/bin/bash" in result:
#             logging.debug("Director found! {}".format(pod))
#             pod_director = pod
#             break
#         else:
#             logging.debug("Director not found! {}".format(pod))
#
#     return pod_director

def find_leader_director(actors):
    filter = "daemon_director.py"
    return  find_node(nodes=actors, kind='director', filter=filter)

def find_running_actor(actors, script):
    return  find_node(nodes=actors, kind='actor', filter=script)

def tqdm_sleep(secs):
    for i in tqdm(range(int(secs)), "Waiting {} secs.".format(secs)):
        sleep(1)


def main():
    # arguments
    parser = argparse.ArgumentParser(description='ICN Stage - Play TCP')

    help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
    parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

    # help_msg = "duration secs (default={})".format(DEFAULT_DURATION_SECS)
    # parser.add_argument("--duration", "-d", help=help_msg, default=DEFAULT_DURATION_SECS, type=int)

    help_msg = "interval milliseconds (default={})".format(DEFAULT_INTERVAL_MILLISENCONDS)
    parser.add_argument("--interval", "-i", help=help_msg, default=DEFAULT_INTERVAL_MILLISENCONDS, type=int)

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
    #logging.info("\t duration secs : {}".format(args.duration))
    logging.info("\t interval milli: {}".format(args.interval))
    logging.info("")
    logging.info("CALCULATED")
    logging.info("---------------------")
    logging.info("\t try name      : {}".format(try_name))
    logging.info("\t results_dir   : {}".format(results_dir))
    logging.info("")

    
    experiments = []



    ##1. benchmark: sem falha
    # experiments += [Experiment(actors=1, directors=1, fails_actors=0, fails_directors=0,
    #                            name="ndn_traffic_Peça_sem_falha")]
    #
    # # #2. problema 1: com falha de ator, sem backup
    # experiments += [Experiment(actors=1, directors=1, fails_actors=1, fails_directors=0,
    #                            name="ndn_traffic_Peça_com_falha")]
    #
    #
    # #3. solução 1: com falha de ator, com backup
    experiments += [Experiment(actors=2, directors=1, fails_actors=1, fails_directors=0,
                               name="ndn_traffic_Peça_com_falha_e_recuperação")]
    # #
    # #
    # # #4. problema 2: com falha de ator e diretor, sem backup de diretor (e backup de ator)
    # experiments += [Experiment(actors=2, directors=1, fails_actors=1, fails_directors=1,
    #                            name="ndn_traffic_Peça_com_falha_diretor")]
    # #
    # # #5. problema 2: com falha de ator e diretor, com backup de diretor (e backup de ator)
    # experiments += [Experiment(actors=2, directors=3, fails_actors=1, fails_directors=1,
    #                            name="ndn_traffic_Peça_com_falha_e_recuperação_diretor")]

    plot_files = ""
    cmd = "kubectl delete pod --all"
    setup_kubernetes.run_cmd(cmd)
    for e in experiments:
        setup_kubernetes.header("Experiment: {}".format(e))
         
        cmd = "python3 setup_kubernetes.py --actors {} --directors {} --log {}".format(e.actors, e.directors, args.log)
        setup_kubernetes.run_cmd(cmd)
        logging.info("Running STEP 0 a - wait after config nodes {}".format(60))
        tqdm_sleep(60)

        director_leader = "director1"
        k8s_cmd = "icn-stage/cli.py addactors".format(args.log)
        setup_kubernetes.run_cmd_kubernete(director_leader, k8s_cmd)
        logging.info("Running STEP 0 b - wait after add actors {}".format(120))
        tqdm_sleep(60)

        start_time = datetime.now()
        start_time = start_time.replace(second=0, microsecond=0)
        start_time += timedelta(seconds=60*5)
        
        k8s_cmd = "python3 icn-stage/cli.py traffic"
        k8s_cmd += " {}".format(start_time.strftime(TIME_FORMAT))
        k8s_cmd += " {}".format(STEP_TIME_SECS*3)
        k8s_cmd += " {}".format(args.interval)
        
        setup_kubernetes.run_cmd_kubernete(director_leader, k8s_cmd)

        logging.info("Running STEP 0 c - wait for finding nodes {}".format(60))
        tqdm_sleep(60)

        if e.directors > 1:
            logging.info("\tFinding leader director...")
            director_leader = find_leader_director(e.directors)
        logging.info("\tLeader director: {}".format(director_leader))

        running_actor = None
        logging.info("\tFinding occupied actor")
        count = 0
        while running_actor is None:
            running_actor = find_running_actor(e.actors, "traffic_ndn_consumer.py")
            sleep(1)
            count += 1
            if count >2:
                sys.exit(-1)
        logging.info("\tOccupied actor: {}".format(running_actor))


        
        now = datetime.now()
        wait = (start_time - now)

        ####################################################
        logging.info("Running STEP 0 d - wait for start time: {}".format(start_time))
        logging.info("wait: {}".format(wait))
        tqdm_sleep(wait.seconds)

        ####################################################
        logging.info("Running STEP 1 - warming up")
        tqdm_sleep(STEP_TIME_SECS*1)

        ##########################################################
        logging.info("Running STEP 2 - failed director")
        if e.fails_directors > 0:
            cmd = "kubectl delete pod {}".format(director_leader)
            setup_kubernetes.run_cmd(cmd)
            logging.info("\t fail directors done {}".format(director_leader))
        else:
            logging.info("\t Skipping fail director")


        step2_finish_time = start_time + timedelta(seconds=STEP_TIME_SECS*2)
        now = datetime.now()
        wait = (step2_finish_time - now)
        logging.info("Running STEP 2 - wating step2_finish_time: {}".format(step2_finish_time))
        logging.info("wait: {}".format(wait))
        tqdm_sleep(wait.seconds)

        ##########################################################
        logging.info("Running STEP 3 - failed actor")
        #fail actor if need
        if e.fails_actors > 0:
            actor_file = "{}/{}_{}.txt".format(results_dir, e.name, running_actor)
            cmd = "kubectl cp {}:/tmp/ndn_traffic_receiver_output.txt {}".format(running_actor, actor_file)
            setup_kubernetes.run_cmd(cmd, check=False)
            logging.info("\t Getting Result: {}".format(actor_file))
            
            cmd = "kubectl delete pod {}".format(running_actor)
            setup_kubernetes.run_cmd(cmd)
            logging.info("\t fail actor done {}".format(running_actor))
        else:
            logging.info("\t Skipping fail actor")


        step3_finish_time = start_time + timedelta(seconds=STEP_TIME_SECS*3)
        now = datetime.now()
        wait = (step3_finish_time - now)
        logging.info("Running STEP 3 - wating step3_finish_time: {}".format(step3_finish_time))
        logging.info("wait: {}".format(wait))
        tqdm_sleep(wait.seconds)


        logging.info("Experiment finished {}!".format(e.name))
        logging.info("Planned: {}    Now: {}".format(start_time + timedelta(seconds=STEP_TIME_SECS*3), datetime.now()))
        result_file = "{}/{}.txt".format(results_dir, e.name)

        cmd = "kubectl cp publisher1:/tmp/daemon_ndn_publisher.stdout {}".format(result_file)
        setup_kubernetes.run_cmd(cmd)
        logging.info("\t Getting Result: {}".format(result_file))

        for a in range(1, e.actors+1):
            try:
                actor_file = "{}/{}_actor{}.txt".format(results_dir, e.name, a)
                cmd = "kubectl cp actor{}:/tmp/ndn_traffic_receiver_output.txt {}".format(a, actor_file)
                setup_kubernetes.run_cmd(cmd, check=False)
                logging.info("\t Getting Result: {}".format(actor_file))
            except Exception as e:
                logging.info("\t Exception: {}".format(e))
                #pass

        tqdm_sleep(60)
        plot_files += " {}".format(result_file)
        
        #wait 60 sec
        #finish
        # cmd = "mv /tmp/daemon_ndn_publisher.stdout /tmp/daemon_ndn_publisher.stdout_{}".format(e.name)
        # setup_kubernetes.run_cmd_kubernete(cmd)


        cmd = "kubectl delete pod --all"
        setup_kubernetes.run_cmd(cmd)

        choosen_actor = ""

    cmd = "python3 plot/plot.py -x {} -o {}/{} {}".format((STEP_TIME_SECS*3+60), results_dir, try_name, plot_files)
    setup_kubernetes.run_cmd(cmd)

if __name__ == '__main__':
    sys.exit(main())