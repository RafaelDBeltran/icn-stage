#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import argparse
import sys

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


def sshd( network, cmd='/usr/sbin/sshd', opts='-D',
          ip='10.123.123.1/32', routes=None, switch=None ):
    """Start a network, connect it to root ns, and run sshd on all hosts.
       ip: root-eth0 IP address in root namespace (10.123.123.1/32)
       routes: Mininet host networks to route to (10.0/24)
       switch: Mininet switch to connect to root namespace (s1)"""
    if not switch:
        switch = network[ 's1' ]  # switch to use
    if not routes:
        routes = [ '10.0.0.0/24' ]
    connectToRootNS( network, switch, ip, routes )
    for host in network.hosts:
        host.cmd( cmd + ' ' + opts + '&' )
    info( "*** Waiting for ssh daemons to start\n" )
    for server in network.hosts:
        waitListening( server=server, port=22, timeout=5 )

    info( "\n*** Hosts are running sshd at the following addresses:\n" )
    for host in network.hosts:
        info( host.name, host.IP(), '\n' )
    info( "\n*** Type 'exit' or control-D to shut down network\n" )
    # CLI( network )
    # for host in network.hosts:
    #     host.cmd( 'kill %' + cmd )
    # network.stop()

if __name__ == '__main__':
    setLogLevel('info')

    parser = argparse.ArgumentParser()
    parser.add_argument('--face-type', dest='faceType', default='udp', choices=['udp', 'tcp'])
    parser.add_argument('--routing', dest='routingType', default='link-state',
                         choices=['link-state', 'hr', 'dry'],
                         help='''Choose routing type, dry = link-state is used
                                 but hr is calculated for comparision.''')

    net = Mininet(switch=OVSKernelSwitch,
                  controller=OVSController, waitConnected=True)

    info('*** Adding controller\n')
    net.addController('c0')


    info('*** Adding NAT\n')
    nat = net.addHost('nat', cls=NAT, ip='10.0.0.99', inNamespace=False)

    #net = Mininet()
    h1 = net.addHost('h1',ip='10.0.0.1', inNamespace=True)
    h2 = net.addHost('h2',ip='10.0.0.2', inNamespace=True)
    #c = net.addHost('c',ip='10.0.0.3', inNamespace=True)

    switch = net.addSwitch('s1')

    # Add links
    host_link = partial(TCLink, bw=1)
    net.addLink(h1, switch, cls=host_link)
    net.addLink(h2, switch, cls=host_link)
    #net.addLink(c, switch)
    net.addLink(nat, switch)

    net.start()

    cmd = '/usr/sbin/sshd'
    opts = '-D'

    info("\n*** starting SSH daemons\n")
    for host in net.hosts:
        host.cmd( cmd + ' ' + opts + '&' )

    info("\n*** Type 'exit' or control-D to shut down network\n")
    CLI(net)

    for host in net.hosts:
        host.cmd( 'kill %' + cmd )

    net.stop()