
import argparse
import sys


from mininet.log import setLogLevel, info
from mininet.topo import Topo

from minindn.minindn import Minindn
from minindn.util import MiniNDNCLI
from minindn.apps.app_manager import AppManager
from minindn.apps.nfd import Nfd
from minindn.apps.nlsr import Nlsr
from minindn.helpers.ndn_routing_helper import NdnRoutingHelper

if __name__ == '__main__':
    setLogLevel('info')

    Minindn.cleanUp()
    #Minindn.verifyDependencies()

    parser = argparse.ArgumentParser()
    parser.add_argument('--face-type', dest='faceType', default='udp', choices=['udp', 'tcp'])
    parser.add_argument('--routing', dest='routingType', default='link-state',
                         choices=['link-state', 'hr', 'dry'],
                         help='''Choose routing type, dry = link-state is used
                                 but hr is calculated for comparision.''')
    topo = Topo()
    a = topo.addHost('a',ip='10.0.0.1', inNamespace=False) #Servidor
    b = topo.addHost('b',ip='10.0.0.2', inNamespace=False) #client
    c = topo.addHost('c',ip='10.0.0.3', inNamespace=False) #client Fail
    topo.addLink(a, b, delay='10ms')
    topo.addLink(a, c, delay='10ms')

    ndn = Minindn(parser=parser, topo=topo)

    ndn.start()
    MiniNDNCLI(ndn.net)

    ndn.stop()
