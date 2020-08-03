#
#   @author: Nelson Antonio Antunes Junior
#   @email: nelson.a.antunes at gmail.com
#   @date: (DD/MM/YYYY) 27/01/2017
import argparse
import os, sys, time, logging, time
from modules.extralib.daemon import Daemon
from modules.worklib.worker_client import *

LOG_LEVEL = logging.DEBUG
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
ACTOR_CONFIG = "info.cfg"
DEFAULT_SLEEP_SECONDS = 5

if LOG_LEVEL == logging.DEBUG:
	logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
						datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')
else:
	logging.basicConfig(format='%(asctime)s %(message)s',
						datefmt=TIME_FORMAT, level=LOG_LEVEL, filemode='w')


class WorkerDaemon(Daemon):
	def __init__(self, pidfile, sleep_seconds=DEFAULT_SLEEP_SECONDS, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
		super().__init__(pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null')
		self.sleep_seconds = sleep_seconds

	def run(self):

		cfg = WorkerClient.load_config_file(ACTOR_CONFIG)
		wclient = WorkerClient(cfg["server"], cfg["hostname"])
		wclient.exp_load()
		last_timestamp = time.time()

		while True:
			busy = False
			actual_timestamp = time.time()
			try:
				for exp_obj in wclient.current_experiments:
					busy = True
					if exp_obj.is_finished():
						wclient.exp_finished(exp_obj)
					elif exp_obj.is_running() and exp_obj.is_snapshot:
						exp_obj.snapshot._save()
					elif not (exp_obj.is_finished() or exp_obj.is_running()) and exp_obj.is_started():
						exp_obj.run(WorkerClient(cfg["server"]))

				if wclient.current_experiments == []:
					busy = False

				wclient.worker_keep_alive(actual_timestamp - last_timestamp, busy)

			except:
				os._exit(1)

			last_timestamp = actual_timestamp
			time.sleep(self.sleep_seconds)


# def main_old():
# 	daemon_cmd = sys.argv[1]
# 	daemon_id = ""
# 	pidfile = "/tmp/daemon_worker_%s.pid"%daemon_id
# 	stdin = "/tmp/daemon_worker_%s.stdin"%daemon_id%daemon_id
# 	stdout = "/tmp/daemon_worker_%s.stdout"%daemon_id%daemon_id
# 	stderr = "/tmp/daemon_worker_%s.stderr"%daemon_id%daemon_id
#
# 	daemon = WorkerDaemon(pidfile=pidfile, stdin=stdin, stdout=stdout, stderr=stderr)
#
# 	if daemon_cmd == 'start':
# 		daemon.start()
# 		daemon_pid = daemon.getpid()
#
# 		if not daemon_pid:
# 			logging.debug("Unable run daemon")
# 		else:
# 			logging.debug ("Daemon is running [PID=%d]" % daemon_pid)
#
# 	elif daemon_cmd == 'stop':
# 		logging.debug ("Stoping daemon")
# 		daemon.stop()
#
# 	elif daemon_cmd == 'restart':
# 		logging.debug ("Restarting daemon")
# 		daemon.restart()
#
# 	elif daemon_cmd == 'status':
# 		daemon_pid = daemon.getpid()
#
# 		if not daemon_pid:
# 			logging.debug ("Daemon isn't running")
# 		else:
# 			logging.debug ("Daemon is running [PID=%d]" % daemon_pid)


def main():
	# arguments
	parser = argparse.ArgumentParser(description='Daemon Worker')

	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

	help_msg = "sleep_seconds (default={})".format(DEFAULT_SLEEP_SECONDS)
	parser.add_argument("--sleep", "-s", help=help_msg, default=DEFAULT_SLEEP_SECONDS, type=int)

	help_msg = "unique id (str) for multiple daemons"
	parser.add_argument("--id", "-i", help=help_msg, default="default", type=str)

	cmd_choices = ['start', 'stop', 'restart', 'status']
	parser.add_argument('cmd', choices=cmd_choices)

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
	logging.info("INPUT")
	logging.info("---------------------")
	logging.info("\t logging level : %s" % args.log)
	logging.info("\t unique id     : %s" % args.id)
	logging.info("\t command option: %s" % args.cmd)
	logging.info("\t sleep seconds : {}".format(args.sleep))
	logging.info("")

	pid_file = "/tmp/daemon_worker_%s.pid" % args.id
	stdout = "/tmp/daemon_worker_%s.stdout" % args.id
	stderr = "/tmp/daemon_worker_%s.stderr" % args.id

	logging.info("FILES")
	logging.info("---------------------")
	logging.info("\t pid_file      : %s" % pid_file)
	logging.info("\t stdout        : %s" % stdout)
	logging.info("\t stderr        : %s" % stderr)
	logging.info("\t config_file   : %s" % ACTOR_CONFIG)

	logging.info("")

	worker_daemon = WorkerDaemon(pid_file, sleep_seconds=args.sleep, stdout=stdout, stderr=stderr)

	# process input parameters
	if args.cmd == 'start':
		worker_daemon.start()
		daemon_pid = worker_daemon.getpid()

		if not daemon_pid:
			logging.info("Unable run daemon")
		else:
			logging.info("Daemon is running [PID=%d]" % daemon_pid)

	elif args.cmd == 'stop':
		logging.info("Stopping worker daemon")
		worker_daemon.stop()

	elif args.cmd == 'restart':
		logging.info("Restarting worker daemon")
		worker_daemon.restart()

	elif args.cmd == 'status':
		daemon_pid = worker_daemon.getpid()

		if not daemon_pid:
			logging.info("Worker Daemon (id='%s') isn't running" % (args.id))
		else:
			logging.info("Worker Daemon (id='%s') is running [PID=%d]" % (args.id, daemon_pid))


if __name__ == '__main__':
	sys.exit(main())
