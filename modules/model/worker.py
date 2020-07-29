#
#   @author: Nelson Antonio Antunes Junior
#   @email: nelson.a.antunes at gmail.com
#   @date: (DD/MM/YYYY) 08/02/2017

import ast
# import logging

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s\t%(message)s', datefmt="%Y-%m-%d %H:%M:%S",filename='daemon_controller.log', filemode='w')


class Worker(object):
	"""docstring for Worker"""
	def __init__(self, hostname, username, path="", password="", pkey="", status="", actors=[], active_time=0.0, failures=0, disconnection_time=0.0, connection_time=0, actor_id="default"):
		self.path = path
		self.hostname = hostname
		self.username = username
		self.password= password
		self.pkey = pkey
		self.status = status

		self.active_time = active_time
		self.failures = failures
		self.disconnection_time = disconnection_time
		self.connection_time = connection_time
		self.actors = actors
		self.actor_id = actor_id


	@staticmethod
	def decode(encoded_worker):
		
		worker_dict = ast.literal_eval(encoded_worker)
		# logging.debug(type(encoded_worker))
		# logging.debug('Literal_Debug: ' + encoded_worker)
		worker = Worker(worker_dict["hostname"], worker_dict["username"], path=worker_dict["path"], password=worker_dict["password"], pkey=worker_dict["pkey"], status=worker_dict["status"], actor_id=worker_dict["actor_id"])

		return worker

	def id(self):
		if self.path != "":
			return self.path.split("/")[-1]
		return None

	def __str__(self):
		return str({"path": self.path,
					"hostname": self.hostname,
					"actor_id": self.actor_id,
					"username": self.username,
					"password": self.password,
					"pkey": self.pkey,
					"status": self.status})

	#"pkey": "{}...{}".format(self.pkey[:10], self.pkey[-10:]),
	def encode(self):
		return str(self).encode()