#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-
import os
import sys
import shlex

import matplotlib.pyplot as plt
import subprocess
import argparse
import logging

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
Y_LIM = 1.0
X_LIM = 600

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_OUT_FILE_NAME = "result"

def defTableu():
	tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
				 (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
				 (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
				 (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
				 (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]
	for i in range(len(tableau20)):
		r, g, b = tableau20[i]
		tableau20[i] = (r / 255., g / 255., b / 255.)
	return tableau20


def process(data):
	result_x = []
	result_y = []
	for line in data:
		try:
			value_x = line.split(" ")[0]
			# format HH:MM:SS example 00:02:59
			value_x = (int(value_x.split(":")[0])*60*60) + (int(value_x.split(":")[1])*60) + (int(value_x.split(":")[2]))
			print("{} {}".format( line.split(" ")[0], value_x))
			value_y = float(line.split(" ")[1])

		except Exception as e:
			logging.error("Exception while reading line: {}".format(line))
			#logging.error("Exception: {}".format(e))
			continue

		result_x += [value_x]
		result_y += [value_y]

	return result_x, result_y


def plotLine(dataset, fileout, xlim, ylim):
	tableau20 = defTableu()

	plots = len(dataset.keys())
	logging.info("number of plots: {}".format(plots))
	fig = plt.figure(figsize=(12, 9))
	#fig, axs = plt.subplots(plots, figsize=(12, 9), sharex=True, sharey=True)
	#fig.set_size_inches(12, 12)
	width = 0.35

	i = 1
	logging.info("Processing {}".format(plots))
	logging.info("-------------")
	for key in dataset.keys():
		logging.debug("key : {}".format(key))

		data = dataset[key]
		logging.debug("data: {}".format(data))

		x_axis, y_axis = process(data)
		#logging.debug("x_axis: {}".format(x_axis))
		#logging.debug("y_axis: {}".format(y_axis))

		#ax = fig.add_subplot("{}1{}".format(plots, i), sharex=True, sharey=True)
		ax = fig.add_subplot(plots, 1, i)
		#axs[i].spines["left"].set_visible(False)
		#axs[i].spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		#ax.set_title(key)
		ax.set_ylabel("Mbits/sec")
		if i == plots:
			ax.set_xlabel("seconds")
		ax.set_xlim([0, xlim])
		ax.set_ylim([0.0, ylim])
		#axs[i].bar(x_axis, y_axis, width= color=tableau20[i])
		ax.plot(x_axis, y_axis, label=key, linestyle="-", linewidth=2, color=tableau20[i])
		ax.legend(loc="lower left")
			#, bbox_to_anchor=[0, 1], 				ncol=2, shadow=False, fancybox=False)

		# if self.upperbond >0 : axs[i].plot(dataset.index,[upperbond]* len(dataset.index),"--", lw=2, color="red", alpha=0.5)
		# if self.upperbond >0 : axs[i].plot(dataset.index,[lowerbond]* len(dataset.index),"--", lw=2, color="red", alpha=0.5)
		i += 1

	# plt.title(title)
	logging.info("Plotting {}".format(plots))
	logging.info("-----------")

	for type in ['png', 'pdf']:
		fileout_complete = "{}.{}".format(fileout, type)
		logging.info(" filename: {}".format(fileout_complete))
		plt.savefig(fileout_complete, bbox_inches="tight")


def main():
	parser = argparse.ArgumentParser(description='ICN-Stage experiments plotter')
	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--log", "-l", help=help_msg, default=DEFAULT_LOG_LEVEL, type=int)

	help_msg = "outputfile (default={})".format(DEFAULT_OUT_FILE_NAME)
	parser.add_argument("--out", "-o", help=help_msg, default=DEFAULT_OUT_FILE_NAME, type=str)

	help_msg = "input_file_1 input_file_2 ... input_file_N "
	parser.add_argument('files', type=str, help=help_msg, nargs=argparse.ONE_OR_MORE)

	help_msg = "x axys length (secs) "
	parser.add_argument("--xlim", "-x", help=help_msg, default=X_LIM, type=int)

	help_msg = "y axys length (secs) "
	parser.add_argument("--ylim", "-y", help=help_msg, default=Y_LIM, type=int)

	# read arguments from the command line
	args = parser.parse_args()

	# setup the logging facility
	if args.log == logging.DEBUG:
		logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
							datefmt=TIME_FORMAT, level=args.log)

	else:
		logging.basicConfig(format='%(asctime)s %(message)s',
							datefmt=TIME_FORMAT, level=args.log)

	cmd_base = "awk -F'[ -]+' '/sec/{print $4" "$8}' "

	if len(sys.argv) == 1:
		print("USAGE {} FILE1 FILE2 ... FILE_N".format(__file__))

	else:

		logging.info("Reading files")
		logging.info("-------------")
		print("")

		data_set = {}
		for filename in args.files:

			logging.info("filename    : {}".format(filename))
			cmd = """awk -F'[ -]+' '/sec/{print $1,$9}' %s""" % filename
			#cmd = """awk -F'[ -]+' '/sec/{print $2,$8}' %s""" % filename
			logging.info("cmd         : {}".format(cmd))
			cmd_shlex = shlex.split(cmd)
			logging.info("cmd_shlex   : {}".format(cmd))
			result_process = subprocess.getoutput(cmd)
			#print(result_process)
			result_data = result_process.split("\n")
			data_set[filename] = result_data
			print("")

		logging.info("Plotting")
		logging.info("-------------")
		plotLine(data_set, args.out, args.xlim, args.ylim)


if __name__ == '__main__':
	sys.exit(main())