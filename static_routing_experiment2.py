
import argparse
import sys

from mininet.log import setLogLevel, info
from mininet.net import Mininet
from mininet.cli import CLI

if __name__ == '__main__':
    setLogLevel('info')

    parser = argparse.ArgumentParser()
    parser.add_argument('--face-type', dest='faceType', default='udp', choices=['udp', 'tcp'])
    parser.add_argument('--routing', dest='routingType', default='link-state',
                         choices=['link-state', 'hr', 'dry'],
                         help='''Choose routing type, dry = link-state is used
                                 but hr is calculated for comparision.''')
    net = Mininet()
    a = net.addHost('a',ip='10.0.0.1', inNamespace=False)
    b = net.addHost('b',ip='10.0.0.2', inNamespace=False)
    c = net.addHost('c',ip='10.0.0.3', inNamespace=False)

    net.start()
    CLI(net)
    net.stop()