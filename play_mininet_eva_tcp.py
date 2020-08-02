#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import argparse
import sys
import subprocess

from mininet.log import setLogLevel, info
from mininet.net import Mininet
from mininet.cli import CLI

from functools import partial
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from mininet.nodelib import NAT

ICN_STAGE_CMD = ['python3', 'icn-stage.py']

# Parameters
# bw	bandwidth in b/s (e.g. '10m')
# delay	transmit delay (e.g. '1ms' )
# jitter	jitter (e.g. '1ms')
# loss	loss (e.g. '1' )
# gro	enable GRO (False)
# txo	enable transmit checksum offload (True)
# rxo	enable receive checksum offload (True)
# speedup	experimental switch-side bw option
# use_hfsc	use HFSC scheduling
# use_tbf	use TBF scheduling
# latency_ms	TBF latency parameter
# enable_ecn	enable ECN (False)
# enable_red	enable RED (False)
# max_queue_size	queue limit parameter for netem Helper method: bool -> 'on'/'off'
#


if __name__ == '__main__':
    setLogLevel('info')

    # parser = argparse.ArgumentParser()
    # parser.add_argument('--face-type', dest='faceType', default='udp', choices=['udp', 'tcp'])
    # parser.add_argument('--routing', dest='routingType', default='link-state',
    #                      choices=['link-state', 'hr', 'dry'],
    #                      help='''Choose routing type, dry = link-state is used
    #                              but hr is calculated for comparision.''')

    # cleanning minnet, for the sake of safety
    cmd = ["sudo", "mn", "--clean"]
    subprocess.call(cmd)

    net = Mininet(switch=OVSKernelSwitch,
                  controller=OVSController, waitConnected=True)

    info('*** Adding controller\n')
    net.addController('c0')

    info('*** Adding NAT\n')
    nat = net.addHost('nat', cls=NAT, ip='10.0.0.99', inNamespace=False)

    h1 = net.addHost('h1',ip='10.0.0.1', inNamespace=True)
    h2 = net.addHost('h2',ip='10.0.0.2', inNamespace=True)
    h3 = net.addHost('h3',ip='10.0.0.3', inNamespace=True)

    switch = net.addSwitch('s1')

    # Add links
    #bw in Mbit/s
    host_link = partial(TCLink, bw=1)
    net.addLink(h1, switch, cls=host_link)
    net.addLink(h2, switch, cls=host_link)
    net.addLink(h3, switch, cls=host_link)
    net.addLink(nat, switch)

    net.start()

    info("\n*** starting SSH daemons\n")
    ssh_cmd = '/usr/sbin/sshd'
    opts = '-D'
    for host in net.hosts:
        host.cmd(ssh_cmd + ' ' + opts + '&')

    # start director
    subprocess.call(ICN_STAGE_CMD + ['start'])

    # clean zookeeper tree
    subprocess.call(ICN_STAGE_CMD + ['reset'])

    # start actors
    subprocess.call(ICN_STAGE_CMD + ['addactors'])

    # run simple TCP test
    subprocess.call(ICN_STAGE_CMD + ['test'])

    #info("\n*** Type 'exit' or control-D to shut down network\n")
    #CLI(net)

    info("\n*** stopping SSH daemons\n")
    for host in net.hosts:
        host.cmd('kill %' + ssh_cmd)

    info("\n*** mininet network\n")
    net.stop()