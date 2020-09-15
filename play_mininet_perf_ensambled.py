#!/usr/bin/python2
# -*- coding: iso-8859-15 -*-

# general imports
import argparse
import logging
import os
import sys
import subprocess
import threading
from time import sleep
import commands
import time
import subprocess
from functools import partial
import shlex

# mininet imports
from mininet.log import setLogLevel, info
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.link import TCLink, Intf
from mininet.nodelib import NAT

# constants
ICN_STAGE_CMD = ['python3', 'icn-stage.py']
DEFAULT_RUN_DIRECTOR = True
DEFAULT_RUN_MININET = True
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_LOG_LEVEL = logging.INFO

# SLEEP_SECS_TO_FAIL = 60 * 2
# IPERF_INTERVAL_SECS = 1
# EXPERIMENT_LENGTH_SECS = 60 * 10

SLEEP_SECS_TO_FAIL = 100 * 1
IPERF_INTERVAL_SECS = 1
EXPERIMENT_LENGTH_SECS = 60 * 10
DIRECTOR_SLEEP_SECS = "5"
DEFAULT_FAILED_WORK = 1
DEFAULT_FAILED_CONT = 2
UDP = False

#         FAIL_ACTORS_MODELS [type failed, id node, failure time, failure duration ]

FAIL_ACTORS_MODELS = [[DEFAULT_FAILED_WORK, 1, 100], [DEFAULT_FAILED_WORK, 2, 150], [DEFAULT_FAILED_WORK, 3, 200],
                      [DEFAULT_FAILED_WORK, 4, 250], [DEFAULT_FAILED_WORK, 5, 250], [DEFAULT_FAILED_WORK, 6, 300],
                      [DEFAULT_FAILED_WORK, 1, 400], [DEFAULT_FAILED_WORK, 2, 400], [DEFAULT_FAILED_WORK, 3, 450],
                      [DEFAULT_FAILED_WORK, 1, 500], [DEFAULT_FAILED_WORK, 1, 600], [DEFAULT_FAILED_WORK, 3, 700]]
FAIL_CONTROLLER = [[DEFAULT_FAILED_CONT, 1, 200], [DEFAULT_FAILED_CONT, 2, 300], [DEFAULT_FAILED_CONT, 3, 400],
                   [DEFAULT_FAILED_CONT, 1, 500], [DEFAULT_FAILED_CONT, 2, 550], [DEFAULT_FAILED_CONT, 3, 600]]
DEFAULT_FAIL_LIST  = []
DEFAULT_MULT_FAILED = []
MANAGE_DIRECTOR = False
results = []

def numeric_compare(x, y):
    return x[2] - y[2]
def get_file_name(fail, actors, iperf_interval_secs=IPERF_INTERVAL_SECS, experiment_length_secs=EXPERIMENT_LENGTH_SECS):
    fail_str = "OFF"
    if fail:
        fail_str = "ON"

    recover_str = "OFF"
    if actors > 1:
        recover_str = "ON"

    transport = "_tcp"
    if UDP:
        transport = "_udp"
    name = 'results_fail-{}_recover-{}_interval-{}s_length-{}s{}.txt'.format(fail_str, recover_str, iperf_interval_secs,
                                                                             experiment_length_secs, transport)
    logging.info(" name: {}".format(name))
    return name
def get_host(net, addr):
    result = None
    for host in net.hosts:
        logging.debug("host: {} IP: {}".format(host, host.IP))
        if addr in "{}".format(host.IP):
            result = host
            logging.info("Result host found! source: {} ".format(host))
            return result
    return result
def introduce_fault(net, destination, source=None):
    busy_actor = None  # "10.0.0.1"
    start_time = time.time()

    if source is None:
        cmd = "python3 zookeeper_controller.py"
        logging.info("[CP10.21] commands.getoutput: {}".format(cmd))
        output = commands.getoutput(cmd)

        cmd = "cat busyactor.txt"
        logging.info("[CP10.22] commands.getoutput: {}".format(cmd))
        busy_actor = commands.getoutput(cmd)
        # busy_actor = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=SLEEP_SECS_TO_FAIL)
        logging.info("[CP10.3] busy_actor: '{}'".format(busy_actor))
        source = get_host(net, busy_actor)

    logging.info("\n\n+--- FAIL EVALUATION [CP10.4] \n")
    if source is not None:

        diff_time = time.time() - start_time
        sleep_secs = SLEEP_SECS_TO_FAIL - int(diff_time)
        logging.info("\n\n+--- Sleeping {} secs ...  [CP10.5]".format(sleep_secs))
        sleep(sleep_secs)

        logging.info(
            "+--- introducing fail  [CP10.6]---+ link source: {} destination: {}\n".format(source, destination))
        # net.configLinkStatus(source, destination, 'down')
        net.delLinkBetween(source, destination)
        logging.info("+--- Finish fail ...  [CP10.7]---+\n")
    else:
        raise Exception(" Source not found! ")
def start_mininet():
    logging.info("+--- Begin Mininet [CP02] ---+\n")
    # cleanning minnet, for the sake of safety
    cmd = ["sudo", "mn", "--clean"]
    logging.debug("\t\t subprocess.call cmd: {}".format(cmd))
    subprocess.call(cmd)
    logging.info("")
    logging.info("")
    net = Mininet(switch=OVSKernelSwitch,
                  controller=OVSController, waitConnected=True)

    logging.info('*** Adding controller [CP03] \n')
    net.addController('c0')
    logging.info("")
    logging.info('*** Begin adding NAT & hosts [CP04]\n')
    nat = net.addHost('nat', cls=NAT, ip='10.0.0.99', inNamespace=False)
    h1 = net.addHost('h1', ip='10.0.0.1', inNamespace=True)
    h2 = net.addHost('h2', ip='10.0.0.2', inNamespace=True)
    h3 = net.addHost('h3', ip='10.0.0.3', inNamespace=True)
    h4 = net.addHost('h4', ip='10.0.0.4', inNamespace=True)
    h5 = net.addHost('h5', ip='10.0.0.5', inNamespace=True)
    h6 = net.addHost('h6', ip='10.0.0.6', inNamespace=True)
    h7 = net.addHost('h7', ip='10.0.0.7', inNamespace=True)
    h8 = net.addHost('h8', ip='10.0.0.8', inNamespace=True)
    h9 = net.addHost('h9', ip='10.0.0.9', inNamespace=True)

    logging.info('*** End Adding NAT & hosts [CP04.done]\n')

    logging.info('*** Adding switch and links [CP05]\n')
    s1 = net.addSwitch('s1')

    logging.info('*** Begin adding links [CP06]\n')
    # Add links
    # bw in Mbits/sec
    host_link = partial(TCLink, bw=1)
    net.addLink(h1, s1, cls=host_link)
    net.addLink(h2, s1, cls=host_link)
    net.addLink(h3, s1, cls=host_link)
    net.addLink(h4, s1, cls=host_link)
    net.addLink(h5, s1, cls=host_link)
    net.addLink(h6, s1, cls=host_link)
    net.addLink(h7, s1, cls=host_link)
    net.addLink(h8, s1, cls=host_link)
    net.addLink(h9, s1, cls=host_link)

    net.addLink(nat, s1)
    logging.info('*** End adding switch and links [CP06.done]\n\n')

    logging.info('Starting network [CP07]\n')
    net.start()
    logging.info("")
    logging.info("")

    logging.info("+--- starting SSH daemons [CP08] ---+\n")
    ssh_cmd = '/usr/sbin/sshd -D &'
    for host in net.hosts:
        logging.info("host: {} ssh_cmd: {}".format(host, ssh_cmd))
        host.cmd(ssh_cmd)
    logging.info("+--- starting SSH daemons done [CP08.done]\n\n")

    return net, h1, h2, h3, h4, h5, h6, h7, h8, h9, s1

def run_play(net, h1, h2, h3, h4, h5, h6, h7, h8, h9, s1, fail_actors):
    fail = fail_actors[0]
    actors = fail_actors[1]

    logging.info("+--- Begin Evaluation [CP09] ---+\n")
    # # clean zookeeper tree
    cmd = ICN_STAGE_CMD + ['reset']
    logging.info("+--- Clean zookeepeer tree [CP09.1] call: {}\n".format(" ".join(cmd)))
    subprocess.call(cmd)
    logging.info("+--- Clean zookeepeer done [CP09.1.done]\n\n")

    # start actors
    cmd = ICN_STAGE_CMD + ['addactors', str(actors)]
    logging.info("+--- Adding actors [CP09.2] call: {}".format(" ".join(cmd)))
    subprocess.call(cmd)
    logging.info("+--- Adding actors done [CP09.2.done]\n\n")

    fault_thread = None
    try:
        if fail:
            logging.info("+--- FAIL EVALUATION [CP10.1fail] ---+\n")
            # run TCP iperf
            # fail_thread = threading.Thread(target=introduce_fault, args=(None, None))
            if actors == 1:
                fault_thread = threading.Thread(target=introduce_fault, args=(net, s1, h1,))
            else:
                fault_thread = threading.Thread(target=introduce_fault, args=(net, s1,))
            fault_thread.start()
        else:
            logging.info("+--- NO FAIL EVALUATION [CP10.2nofail] ---+\n")

        transport = "tcp"
        if UDP:
            transport = "udp"
        cmd = ICN_STAGE_CMD + ['iperf', get_file_name(fail, actors), str(IPERF_INTERVAL_SECS),
                               str(EXPERIMENT_LENGTH_SECS), transport]
        logging.info("[CP10.7] call: {}".format(" ".join(cmd)))
        subprocess.call(cmd)
        # popen = subprocess.Popen(cmd)

        logging.info("")
        logging.info("")

    except Exception as e:
        print("Exception: {} \n\n\n".format(e))

    finally:
        if fault_thread is not None:
            logging.info("waiting for join fail thread... [CP10.5] timeout=---+\n")
            fault_thread.join()
        logging.info("")
        logging.info("")
def stop_director():
    # stop director
    cmd = ICN_STAGE_CMD + ['stop']
    logging.info("Stopping director... [CP11] {}\n".format(" ".join(cmd)))
    subprocess.call(cmd)
    logging.info("")
    logging.info("")
    # stop director
    stop_script("daemon_director.py")

    cmd = "rm -f /tmp/daemon_director_default.pid"
    logging.info("\t+--- Removing director pid cmd: {}".format(cmd))
    commands.getoutput(cmd)
    logging.info("\t+--- Stopping director(s)... done. [CP-2.done] ")
def start_director():
    # start director
    logging.info("\t+--- Starting director... [CP-1]")
    cmd = ICN_STAGE_CMD + ['start', "--sleep", DIRECTOR_SLEEP_SECS]
    logging.debug("subprocess.call: {}".format(cmd))
    subprocess.call(cmd)
    logging.debug("\t+--- Starting director done. [CP-1.done] \n\n")
def stop_script(script):
    cmd = "pgrep -f '{}' ".format(script)
    results = commands.getoutput(cmd)
    for pid in results.split("\n"):
        cmd = "sudo kill {} -SIGKILL".format(pid)
        logging.info("\t+--- Stopping script cmd: {}".format(cmd))
        commands.getoutput(cmd)
def stop_workers():
    stop_script("daemon_worker.py")
def stop_iperf():
    logging.info("Stopping iperf server... [CP12] \n")
    stop_script("iperf")

    logging.info("Stopping iperf client... [CP13]\n")
    stop_script("iperf_client.py")
    logging.info("")
    logging.info("")
def stop_mininet(net):
    logging.info("+--- begin stopping SSH daemons [CP13] ---+\n")
    for host in net.hosts:
        cmd = 'kill /usr/sbin/sshd'
        logging.info("\t\t host: {} cmd: {}".format(host, cmd))
        host.cmd(cmd)
    logging.info("+--- end stopping SSH daemons [CP13.done] ---+\n")

    logging.info("+--- Stopping mininet network [CP14]---+\n")
    net.stop()
def delete_actors_storage():
    # delete actors
    logging.info("+--- Deleting actors storage [CP-3] ---+")
    for a in range(3):
        cmd = "rm -rf ~/actor_mininet_{}".format((a + 1))
        logging.info("\t\t cmd: {}".format(cmd))
        subprocess.call(cmd, shell=True)
    cmd = "rm -f /tmp/daemon_worker_*"
    logging.info("\t\t cmd: {}".format(cmd))
    logging.debug("+--- End Deleting actors storage [CP-3.done] ---+\n")





def main():
    # parse arguments
    parser = argparse.ArgumentParser(description='*** An Iperf based ICN-Stage Play ***')

    help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
    parser.add_argument("--log", "-l", help=help_msg, default=DEFAULT_LOG_LEVEL, type=int)

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
    logging.info("SETTINGS")
    logging.info("---------------------")
    logging.info("\t Logging level : {}".format(args.log))
    logging.info("\t Fail Actors   : {}".format(FAIL_ACTORS_MODELS))
    logging.info("\n")

    delete_actors_storage()

    cmd = "python3 icn_stage.py setconfig ensambled"
    subprocess.call(cmd, shell=True)
    net, h1, h2, h3, h4, h5, h6, h7, h8, h9, s1 = start_mininet()
    cmd = 'python3 icn_stage.py addcontrollers 3'
    subprocess.call(cmd, shell=True)
    exit()

#    for fail_actors in FAIL_ACTORS_MODELS:

        # Reset

#       if MANAGE_DIRECTOR:
#            stop_director()
#            MANAGE_DIRECTOR = True
#
#       if not MANAGE_DIRECTOR:
#            start_director()

        #logging.info("\n\n\n\n")
        #logging.info(" ({}/{}) FAIL? ACTORS?: {}".format(count_fail, len(FAIL_ACTORS_MODELS), fail_actors))
       # logging.info("---------------------\n")
        #stop_iperf()
       # stop_workers()
       # results += [get_file_name(fail_actors[0], fail_actors[1])]
        #run_play(net, h1, h2, h3, h4, h5, h6, h7, h8, h9, s1, fail_actors)
        #logging.info("---------------------\n")
        #logging.info(" ({}/{}) DONE FAIL? ACTORS?: {}\n\n\n".format(count_fail, len(FAIL_ACTORS_MODELS), fail_actors))
       # count_fail += 1

        #stop_mininet(net)

    #if MANAGE_DIRECTOR:
     #   stop_director()

   # stop_iperf()
   # stop_workers()

    transport = "tcp"
    if UDP:
        transport = "udp"

    logging.info("")
    logging.info("PLOTTING")
    logging.info("---------------------")
    fileout = "result_interval-{}s_length-{}s_dirsleep-{}_{}".format(IPERF_INTERVAL_SECS, EXPERIMENT_LENGTH_SECS,
                                                                     DIRECTOR_SLEEP_SECS, transport)
    cmd = "python3 plot.py --xlim {} --out {} ".format(EXPERIMENT_LENGTH_SECS, fileout)
    for result in results:
        cmd += " " + result

    logging.info("cmd         : {}".format(cmd))
    cmd_shlex = shlex.split(cmd)
    logging.debug("cmd_shlex   : {}".format(cmd_shlex))
    subprocess.call(cmd_shlex)
    logging.info("cmd         : {}".format(cmd))


# subprocess.call(cmd)
if __name__ == '__main__':
    sys.exit(main())
