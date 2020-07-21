"""Exemplos de topologias

   Adding the 'topos' dict with a key/value pair to generate our newly defined
	topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

from mininet.nodelib import NAT


class MyTopo(Topo):
	"""Simple topology example.
	Two directly connected switches plus a host for each switch:

	   host --- switch --- switch --- host

	Adding the 'topos' dict with a key/value pair to generate our newly defined
	topology enables one to pass in '--topo=mytopo' from the command line.
	"""

	def __init__(self):
		"Create custom topo."

		# Initialize topology
		Topo.__init__(self)

		# Add hosts and switches
		leftHost = self.addHost('h1')
		rightHost = self.addHost('h2')
		leftSwitch = self.addSwitch('s3')
		rightSwitch = self.addSwitch('s4')

		# Add links
		self.addLink(leftHost, leftSwitch)
		self.addLink(leftSwitch, rightSwitch)
		self.addLink(rightSwitch, rightHost)


class Linear_3s3h(Topo):
	"""Exemplo do trabalho
	3 switches, cada um com um host atrelado

	 switch1 --- switch2 --- switch3
		|           |           |
	  host1       host2       host3

	"""

	def __init__(self):
		"Create custom topo."

		# Initialize topology
		Topo.__init__(self)

		info('*** Add switches\n')
		s1 = self.addSwitch('s1', cls=OVSKernelSwitch)
		s2 = self.addSwitch('s2', cls=OVSKernelSwitch)
		s3 = self.addSwitch('s3', cls=OVSKernelSwitch)

		info('*** Add hosts\n')
		h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)
		h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
		h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)

		info('*** Add links\n')
		self.addLink(s1, h1)
		# h2s2 = {'delay':'10ms'}
		# self.addLink(h2, s2, cls=TCLink , **h2s2)
		self.addLink(h2, s2)
		# h3s3 = {'loss':10}
		# self.addLink(h3, s3, cls=TCLink , **h3s3)
		self.addLink(h3, s3)
		self.addLink(s1, s2)
		self.addLink(s2, s3)


class Linear_3s2h1n(Topo):
	"""Exemplo do trabalho
	3 switches: dois primeiros com um host atrelado e o terceiro com a NAT

	 switch1 --- switch2 ---  switch3
	   |           |            |
	 host1       host2        nat1

	"""

	def __init__(self):
		"Create custom topo."

		# Initialize topology
		Topo.__init__(self)

		info('*** Add switches\n')
		s1 = self.addSwitch('s1', cls=OVSKernelSwitch)
		s2 = self.addSwitch('s2', cls=OVSKernelSwitch)
		s3 = self.addSwitch('s3', cls=OVSKernelSwitch)

		info('*** Add NAT\n')
		self.natIP = '10.0.0.3'

		nat1 = self.addNode('nat1', cls=NAT, ip=self.natIP,
							inNamespace=False)

		info('*** Add hots\n')
		h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute='via ' + self.natIP)
		h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute='via ' + self.natIP)
		# h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)

		info('*** Add links\n')
		self.addLink(s1, s2)
		self.addLink(s2, s3)

		self.addLink(s1, h1)
		# h2s2 = {'delay':'10ms'}
		# self.addLink(h2, s2, cls=TCLink , **h2s2)
		self.addLink(h2, s2)
	# h3s3 = {'loss':10}
	# self.addLink(h3, s3, cls=TCLink , **h3s3)
	# self.addLink(nat1, s3)


class Star_1s3h(Topo):
	"""Example ICN Stage
	 3 switches: dois primeiros com um host atrelado e o terceiro com a NAT

			 NAT
			  |
	host1 - switch1 --- hos3
	  		  |
	 		host2

	"""

	def __init__(self):
		"Create custom topo."

		# Initialize topology
		Topo.__init__(self)

		info('*** Add switch\n')
		s1 = self.addSwitch('s1', cls=OVSKernelSwitch)

		info('*** Add NAT\n')
		self.natIP = '10.0.0.10'

		nat1 = self.addNode('nat1', cls=NAT, ip=self.natIP,
							inNamespace=False)

		info('*** Add hots\n')
		h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute='via ' + self.natIP, inNamespace=False)
		h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute='via ' + self.natIP, inNamespace=False)
		h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute='via ' + self.natIP, inNamespace=False)

		info('*** Add links\n')
		self.addLink(s1, h1)
		self.addLink(s1, h2)
		self.addLink(s1, h3)
		self.addLink(nat1, s1)
		# h2s2 = {'delay':'10ms'}
		# self.addLink(h2, s2, cls=TCLink , **h2s2)


topos = {'mytopo': (lambda: MyTopo()),
		 'l3s3h': (lambda: Linear_3s3h()),
		 'l3s2h1n': (lambda: Linear_3s2h1n()),
		 'star': (lambda: Star_1s3h())}