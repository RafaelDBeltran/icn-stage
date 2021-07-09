import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from extralib.daemon import Daemon

class DaemonEnsemble(Daemon):

	def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
		super().__init__(pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null')