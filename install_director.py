#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-

# by KaYuÃ@Collaborator ICN-Stage 22/06/2020 %%/ version 1.0.0
import argparse
import os
import re
import json
import subprocess
import sys
import time
import logging

LOG_LEVEL = logging.DEBUG
TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
DEFAULT_SETTINGS_FILE = ""
DEFAULT_REQUIREMENTS_FILE = ""


try:
	from paramiko import SSHClient
	import paramiko

except ImportError as error:

	print(error)
	print()
	print("1. Setup a virtual environment: ")
	print("  python3 - m venv ~/Python3env/icn-stage ")
	print("  source ~/Python3env/icn-stage/bin/activate ")
	print()
	print("2. Install requirements:")
	print("  pip3 install --upgrade pip")
	print("  pip3 install -r requirements.txt \n")
	quit()


class ExtendStdout:
	# $~/doc @info 1
	#
	#       This class is an extension of the standard output
	#       responsible for handling excess and showing information
	#       from the call of your instance.This class implements
	#       error dictionary and special display and error handling
	#       functions.
	#
	#                        raise_exception
	#       This function implements error handling from the code
	#       generated in the event of the call.
	#
	#                           show_info
	#       This function implements the exit interface from the code
	#       generated in the event of the call.

	Intro = """
                            INSTALLER ICN-Stage
                              
         This script is responsible for the installation and configuration
         of the ICN-Stage, the whole process is automatic and you only need
         to instantiate the Servers. For this task, access the settings file
         present in the program settings directory.This script has default
         settings that can be changed through the settings file.
           
         This script allows the installation of ICN-Stage dependencies
         remotely being only necessary to agree to the installation and
         have the connection accepted by the target server.
           
         This script is not responsible for activating the server remotely,
         leaving the controller file to perform this task.
           
         If you find any errors, please contact the developer.


           """

	DefaultError = {
		0x001: "\nERROR: Operation aborted",
		0x002: "\nERROR: The configuration Settings.json file may be corrupted.",
		0x003: "\nERROR: The configuration Requirements.json file may be corrupted.",
		0x004: "\nERROR: Connection refused.",
		0x005: "\nERROR: Server not reached.",
		0x006: "\nERROR: Server unavailable for use.",
		0x007: "\nERROR: Error while generating the settings file remotely.",
		0x008: "\nERROR: Error generating extract file remotely.",
		0x009: "\nERROR: Error while configuring the server."
	}

	DefaultInfoStatus = {
		0x001: "Done\n",
		0x002: " Please Wait: Reading file Settings...",
		0x003: " Contacting Server ID:",
		0x004: " Awaiting Response.Please wait...",
		0x005: "\n Server Reached. Connection established.\n",
		0x006: "\n\n Starting dependency installer. Please wait...\n\n",
		0x007: "\n    Necessary Dependences:\n\n",
		0x008: "\n    Missing Dependences:\n\n",
		0x009: "\n Do you want install all dependences in Server?(YES/NO)",
		0x010: "\n Do you want install ICN-Stage and Apache-Zookeeper in Server?(YES/NO)",
		0x011: "\n ICN-Stage download completed.\n",
		0x012: " Extracting ICN-Stage.\n",
		0x013: " Apache-Zookeeper download complete",
		0x014: " Extraindo  Apache-Zookeeper concluído.\n",
		0x015: "\mGenerated settings file",
		0x016: " Please wait.",
		0x017: " Please Wait: Reading file Requirements...",
		0x018: "\n Download...Done",
		0x019: "\n It has been detected that currently all dependencies are already installed.\n",
		0x020: "\n Downloading ICN-Stage.\n",
		0x021: "\n Downloading Apache-Zookeeper.\n"
	}
	ServerInstance = []

	# def __init__(self):
	#     print(self.Intro)
	#     time.sleep(15)

	@staticmethod
	def raise_exception(ValueException=0x001, CriticalFailure=False, Header=False, Server={}):

		if Header:
			print("\n\nSERVER:", Server[0]['ID'], "\nHOST:", Server[1]['Host'], " USERNAME:", Server[2]['User'], " \n")

		try:
			print(ExtendStdout.DefaultError[ValueException])
			time.sleep(5)

		except:
			print(ExtendStdout.DefaultError[0x001])
			time.sleep(5)

		if CriticalFailure:
			print(ExtendStdout.DefaultError[0x001])
			quit()

	@staticmethod
	def show_info(ValueInfo=0x016, Header=False, Server={}):

		if Header:
			print('\n\nSERVER:', Server[0]['ID'], '\nHOST:', Server[1]['Host'], ' USERNAME:', Server[2]['User'], ' \n')

		try:
			print(ExtendStdout.DefaultInfoStatus[ValueInfo], end="")

		except:
			print(ExtendStdout.DefaultInfoStatus[0x001])


class ZookeeperEnsembleSettings:
	# $~/doc @info 2
	#
	#       This class is resposable for get Settings.
	#
	#                     read_settings_file
	#       This fuction reads the ICN-Stage settings file,
	#       obtaining information regarding the Apache-Zookeeper
	#       settings and the controller server instances. Its
	#       settings can be changed in ~/ICN-Stage/Settings/Settings.json.
	#
	#                    read_requirements_file
	#      This function reads the ICN-Stage dependencies file,
	#      it contains information and addresses of the
	#      dependencies repositories. This file is in the ICN-Stage
	#      ~/Requerements directory and should only be changed
	#      in case of software updates.
	#
	#                     write_settings_file
	#      This function is responsible for preparing the
	#      configuration file in the format necessary for
	#      the interpretation of Apache-Zookeeper.
	#      The settings can be changed through the Dir =
	#      ~/Settings/Settings.json file, or set to default
	#      if there are errors in the configuration file or
	#      it is not found.
	#      Blank configuration fields will be automatically
	#      replaced with default values.
	#
	#
	OutPutSettings = """

#   This Apache Zookeeper software configuration file was
#   automatically generated by ICN-Stage.
#   This file contains information regarding the
#   settings regarding the distributed installation
#   of ICN-State in its basic mode.
#   
#   The information in this file can be changed through
#   the Settings.json file in the ICN-Stage ~/Settings directory.
#   Play the ICN-Stage installation file when changing the file.
#   This file must remain next to the Apache-Zookeeper directory.
   
#   Settings Apache-Zookeeper\n
"""

	ListRequirements = []
	RepositoryICNStage = []
	RepositoryZk = []
	ListServers = []

	SettingsValue = [5, 6000, 12000, 10, 5, 2181, 256]
	SettingsDir = 'Settings.json'
	SettingsZkDir = 'zookeeper-3.4.9/conf/zoo.cfg'
	DataDir = '~/.zk/datadir'
	RequirementsDir = 'Requirements.json'
	Settings = ['TickTime', 'MinSessionTimeOut', 'MaxSessionTimeOut', 'InitLimit',
				'SyncLimit', 'ClientPort', 'MaxClientCnxns']

	def __init__(self):
		ExtendStdout.show_info(0x002, False)
		self.read_settings_file(ExtendStdout)
		ExtendStdout.show_info(0x001, False)
		ExtendStdout.show_info(0x017, False)
		self.read_requirements_file(ExtendStdout)
		ExtendStdout.show_info(0x001, False)

	def read_settings_file(self):

		if os.path.exists(self.SettingsDir):

			with open(self.SettingsDir) as Settings:

				try:
					SettingsFile = json.load(Settings)
					for IdParameter, Parameter in enumerate(self.Settings):
						self.SettingsValue[IdParameter] = (SettingsFile['Settings'][0][Parameter])
					for Iterator in SettingsFile['Server']:
						NewServer = []
						NewServer.append({'ID': Iterator['Id']})
						NewServer.append({'Host': Iterator['Host']})
						NewServer.append({'User': Iterator['UserName']})
						NewServer.append({'Password': Iterator['Password']})
						self.ListServers.append(NewServer)
				except:
					ExtendStdout.raise_exception(0x002, True, False)
		else:
			ExtendStdout.raise_exception(0x002, True, False)

	def read_requirements_file(self):

		if os.path.exists(self.RequirementsDir):

			with open(self.RequirementsDir) as requirements_icn:
				requirements = json.load(requirements_icn)
				self.ListRequirements = requirements['Dependences']
				self.RepositoryZkICN = requirements['Repository']

		else:
			ExtendStdout.raise_exception(0x003, True, False)

	def write_settings_file(self):

		for key, Parameters in enumerate(self.Settings):
			self.OutPutSettings += (str(Parameters) + '=' + str(self.SettingsValue[key]) + '\n')

		for Server in self.ListServers:
			self.OutPutSettings += ('Server.' + Server[0]['ID'] + '=' + Server[1]['Host'] + ':2888:3888\n')
		print(self.OutPutSettings)
		return self.OutPutSettings


class ConnectServers:
	# $~/doc @info 3
	#                       ConnectServers
	#
	#       This class is responsible for creating a communication
	#       channel between the machine managing the installation
	#       and the geographically distributed servers.
	#
	#                       __init__(main)
	#       This fuction allows communication through the SecuritySell
	#       interface and is dependent on Paramiko
	#
	#       This function is responsible for establishing communication
	#       with the SSH interface and maintaining the connection as an
	#       instance.
	#
	#                           Command
	#       This function corresponds to the remote terminal.
	State = False

	def __init__(self, Server, ExtendStdout):

		ExtendStdout.show_info(0x003, True, Server)
		print(Server[0]['ID'])
		ExtendStdout.show_info(0x004, False, Server)

		self.ssh = SSHClient()
		self.ssh.load_system_host_keys()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		try:

			self.ssh.connect(hostname=Server[1]['Host'], username=Server[2]['User'],
							 password=str(Server[3]['Password']))
			self.State = True
			ExtendStdout.show_info(0x005, False, Server)
			time.sleep(2)

		except:
			ExtendStdout.raise_exception(0x004, False, False, Server)
			self.State = False

	def GetStateConnection(self):
		return self.State

	def CloseConnection(self):
		self.State = False
		self.ssh.close()

	def Command(self, cmd):

		try:
			stdin, stdout, stderr = self.ssh.exec_command(cmd)
			return stdout.read()

		except:
			self.State = False


class Installer:
	# $~/doc @info 4
	#                          Installer
	#
	#       This class is responsible for doing the remote
	#       installation of the servers. Its functions include
	#       obtaining repositories,updating packages, finding
	#       missing dependencies, creating directoriesand
	#       configuring servers.
	#
	#                     RemoteListDependences
	#       This function is responsible for contacting remote
	#       machines and obtaining information about dependencies
	#       already installed and missing.
	#
	#                     RemoteInstallDependences
	#       This function is responsible for remotely installing
	#       dependencies known to be missing.
	#
	#                    remote_install_icn_stage
	#       This function is responsible for remotely installing
	#       the ICN-Stage and Apache-Zookeeper.This function is
	#       also responsible for generating the Apache-Zookeeper
	#       configuration file and adding the identification tag.
	#

	DependencesMissing = []
	DependencesMissingBool = False

	def __init__(self, settings):
		self.settings = settings

	def remote_install(self):

		ExtendStdout.show_info(0x006, False)
		for Server in self.settings.ListServers:

			NewServerConnection = ConnectServers(Server, ExtendStdout)

			if NewServerConnection.GetStateConnection():
				DependencesMissing = (self.RemoteListDependences(NewServerConnection, self.settings, Server))
				self.RemoteInstallDependences(NewServerConnection, DependencesMissing, Server)
				self.remote_install_icn_stage(NewServerConnection, Server, self.settings)
				NewServerConnection.CloseConnection()

		DependencesMissing = []

	@staticmethod
	def local_install():
		ExtendStdout.show_info(0x006, False)
	 	#TODO change to a DEFAULT_CONSTANT
		cmd = ["wget", "http://mirror.nbtelecom.com.br/apache/zookeeper/zookeeper-3.6.1/apache-zookeeper-3.6.1-bin.tar.gz"]
		subprocess.run(cmd)

		cmd = ['tar', 'zxf', 'apache-zookeeper-3.6.1-bin.tar.gz']
		subprocess.run(cmd)

	def RemoteListDependences(self, ConnectionServer, Settings, Server, ExtendStdout):

		DependencesMissingCommand = []
		DependencesInstaled = []
		ServerResponse = ConnectionServer.Command(('apt list --installed '))

		if not ConnectionServer.GetStateConnection():
			ExtendStdout.raise_exception(0x005, False, False)

		for Requirements in Settings.ListRequirements[0]:

			if type(re.search(Requirements, str(ServerResponse))) == type(None):
				self.DependencesMissing.append(Requirements)
				DependencesMissingCommand.append(Settings.ListRequirements[0][Requirements])

			else:
				DependencesInstaled.append(Requirements)

		ExtendStdout.show_info(0x007, True, Server)

		for NumDep, Dependences in enumerate(Settings.ListRequirements[0]):
			print('    ', NumDep, ' - ', Dependences)

		ExtendStdout.show_info(0x008, False, None)

		for NumDep, Dependences in enumerate(self.DependencesMissing):
			print('    ', NumDep, ' - ', Dependences)

		return DependencesMissingCommand

	def RemoteInstallDependences(self, Connection, DependencesCommandList, Server, ExtendStdout):

		if len(DependencesCommandList):

			ExtendStdout.show_info(0x009, False)

			if str(input()) == 'YES':

				Connection.Command('mkdir ICN-Stage')
				self.DependencesMissingBool = True
				ls = str(Connection.Command('pwd'))
				ls = ('/' + ls[3:ls.index('n') - 1] + '/ICN-Stage')

				for PArgs, Command in enumerate(DependencesCommandList):
					print('\nDownloading.', Command[10:])
					ExtendStdout.show_info(0x016, False, Server)
					print('', end='')
					Connection.Command(Command)
					dep = self.DependencesMissing[PArgs]
					dep = 'mv ' + dep[8:] + '/' + dep[8:] + ' ' + ls
					Connection.Command(dep)

					ExtendStdout(0x018, False, Server)

			else:

				ExtendStdout.raise_exception(0x006, False, Server)

		else:
			ExtendStdout.show_info(0x019, False, Server)

	def remote_install_icn_stage(self, ConnectionServer, Server, Settings):
		ExtendStdout.show_info(0x010, False, Server)

		if str(input()) == 'YES':
			if not self.DependencesMissingBool:
				ConnectionServer.Command('mkdir ICN-Stage')

			try:
				ExtendStdout.show_info(0x020, False, Server)
				ConnectionServer.Command(Settings.RepositoryZkICN[0]['ICN-Stage'])
				ExtendStdout.show_info(0x011, False, Server)
				ConnectionServer.Command('mv  Jogo-Da-Velha-Java/* ICN-Stage')
				ConnectionServer.Command(Settings.RepositoryZkICN[0]['Apache-Zookeeper'])
				ExtendStdout.show_info(0x021, False, Server)
				ConnectionServer.Command('tar zxf apache-zookeeper-3.6.1-bin.tar.gz ')
				ExtendStdout.show_info(0x014, False, Server)
				ConnectionServer.Command('mkdir ICN-Stage/zookeeper-3.4.9')
				ConnectionServer.Command('mv apache-zookeeper-3.6.1-bin/* ICN-Stage/zookeeper-3.4.9 ')
				ConnectionServer.Command('mv  Jogo-Da-Velha-Java/* ICN-Stage')
				serv = ConnectionServer.Command(
					'echo "' + str(Settings.write_settings_file(ExtendStdout)) + '"> ICN-Stage/zookeeper-3.4.9/conf/zoo.cfg')
				print(serv)
				ExtendStdout.show_info(0x015, False, Server)
				CmdsEcho = ('echo "' + str(Server[0]['ID']) + '" > ICN-Stage/~/.zk/datadir/myid')
				ConnectionServer.Command(CmdsEcho)
				ExtendStdout.show_info(0x001, False, Server)

			except:
				ExtendStdout.raise_exception(0x009, False, False, Server)


def install_zookeeper_ensemble():
	zookeeper_ensemble_settings = ZookeeperEnsembleSettings()
	Installer(zookeeper_ensemble_settings)


def main():
	# arguments
	parser = argparse.ArgumentParser(description='Daemon Worker')

	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

	help_msg = "unique id (str) for multiple daemons"
	parser.add_argument("--id", "-i", help=help_msg, default="default", type=str)

	help_msg = "requirements file"
	parser.add_argument("--requirements", "-r", help=help_msg, default=DEFAULT_REQUIREMENTS_FILE, type=str)

	help_msg = "settings file"
	parser.add_argument("--settings", "-s", help=help_msg, default=DEFAULT_SETTINGS_FILE, type=str)

	install_choices = ['local', 'vagrant', 'remote_single', 'remote_ensemble']
	parser.add_argument('install', choices=install_choices)

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
	logging.info("\t logging level     : %s" % args.log)
	logging.info("\t unique id         : %s" % args.id)
	logging.info("\t install option    : %s" % args.install)
	logging.info("\t requirements file : %s" % args.requirements)
	logging.info("\t settings file     : %s" % args.settings)
	logging.info("")

	settings = ZookeeperEnsembleSettings()
	installer = Installer(settings)

	if args.install == 'local':
		installer.local_install()

	elif args.install == 'vagrant':
		installer.local_install()
		installer.vagrant_config()

	elif args.install == 'remote_single':
		#logging.info("Stopping worker daemon")
		#worker_daemon.stop()
		installer.remote_install()

	elif args.install == 'remote_ensemble':
		logging.info("Stopping worker daemon")
		#worker_daemon.stop()

	#
	# elif args.cmd == 'restart':
	# 	logging.info("Restarting worker daemon")
	# 	worker_daemon.restart()
	#
	# elif args.cmd == 'status':
	# 	daemon_pid = worker_daemon.getpid()
	#
	# 	if not daemon_pid:
	# 		logging.info("Worker Daemon (id='%s') isn't running" % (args.id))
	# 	else:
	# 		logging.info("Worker Daemon (id='%s') is running [PID=%d]" % (args.id, daemon_pid))


if __name__ == '__main__':
	sys.exit(main())

