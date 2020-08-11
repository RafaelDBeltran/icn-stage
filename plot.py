#!/usr/bin/python3
# -*- coding: iso-8859-15 -*-
import os
import sys
import shlex

# import matplotlib.font_manager
# from matplotlib import rcParams
# #rcParams['font.family'] = 'sans-serif'
# rcParams['font.sans-serif'] = ['Verdana']
import matplotlib.pyplot as plt
import subprocess
import argparse
import logging

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
Y_LIM = 1.0
X_LIM = None

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_OUT_FILE_NAME = "result"

key_titles = {}
key_titles["results_fail-OFF_recover-ON"] = "No fault"
key_titles["results_fail-ON_recover-ON"] = "Single fault, and single backup actor"
key_titles["results_fail-ON_recover-OFF"] = "Single fault, and no backup actor"


def get_key(key):

	for k in key_titles.keys():
		if k in key:
			return key_titles[k]

	return key



def defTableu():
	# source: http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/
	# These are the "Tableau 20" colors as RGB.
	tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
				 (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
				 (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
				 (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
				 (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

	# Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
	for i in range(len(tableau20)):
		r, g, b = tableau20[i]
		tableau20[i] = (r / 255., g / 255., b / 255.)
	return tableau20


def process2(data):
	first_value = None
	results = {}
	result_x = []
	result_y = []
	for line in data:
		# it's [SUM] line
		if "Mbits/sec" in line:
			continue

		try:
			clock = line.split(" ")[0]

			# x format: HH:MM:SS example: 00:02:59
			clock = (int(clock.split(":")[0])*60*60) + (int(clock.split(":")[1])*60) + (int(clock.split(":")[2]))
			if first_value is None:
				first_value = clock
			clock -= first_value
			interval_begin = int(float(line.split(" ")[1]) + clock)
			interval_end = int(float(line.split(" ")[2]) + clock)
			value_x = "%03d-%03d" % (interval_begin, interval_end)
			value_y = float(line.split(" ")[3])
			if value_x not in results:
				results[value_x] = value_y
			else:
				results[value_x] += value_y
			print("x:{} y:{} line:'{}'".format(value_x, value_y, line))

		except Exception as e:
			logging.error("Exception while reading line: {} exception: {} ".format(line, e))
			continue

	for k in sorted(results.keys()):
		print("x:{} y:{} ".format(k, results[k]))
		result_x += [k]
		result_y += [results[k]]

	return result_x, result_y


def process(data):
	first_value = None
	result_x = []
	result_y = []
	for line in data:
		# it's [SUM] line
		if "Mbits/sec" in line:
			continue

		try:
			value_x = line.split(" ")[0]

			# x format: HH:MM:SS example: 00:02:59
			value_x = (int(value_x.split(":")[0])*60*60) + (int(value_x.split(":")[1])*60) + (int(value_x.split(":")[2]))
			if first_value is None:
				first_value = value_x

			value_x -= first_value

			value_y = float(line.split(" ")[1])
			logging.debug("{} {} {}".format(line.split(" ")[0], value_x, value_y))

		except Exception as e:
			logging.error("Exception while reading line: {} exception: {} ".format(line, e))
			continue

		result_x += [value_x]
		result_y += [value_y]

	return result_x, result_y


def plot_line(dataset, fileout, xlim, ylim):
	logging.info("PLOT LINE")

	tableau20 = defTableu()

	plots = len(dataset.keys())
	logging.info("number of plots: {}".format(plots))
	fig = plt.figure(figsize=(12, 9))
	fig.rcParams["font.family"] = "serif"
	# fig, axs = plt.subplots(plots, figsize=(12, 9), sharex=True, sharey=True)
	# fig.set_size_inches(12, 12)
	width = 0.35

	i = 1
	logging.info("Processing {}".format(plots))
	logging.info("-------------")
	for key in dataset.keys():
		logging.debug("key : {}".format(key))

		data = dataset[key]
		logging.debug("data: {}".format(data))

		x_axis, y_axis = process(data)
		# logging.debug("x_axis: {}".format(x_axis))
		# logging.debug("y_axis: {}".format(y_axis))

		# ax = fig.add_subplot("{}1{}".format(plots, i), sharex=True, sharey=True)
		ax = fig.add_subplot(plots, 1, i)

		# axs[i].spines["left"].set_visible(False)
		# axs[i].spines["right"].set_visible(False)
		ax.get_xaxis().tick_bottom()
		ax.get_yaxis().tick_left()
		# ax.set_title(key)
		ax.set_ylabel("Bandwidth (Mbits/sec)")
		if i == plots:
			ax.set_xlabel("Running time (seconds)")
		ax.set_xlim([0, xlim])
		ax.set_ylim([0.0, ylim])
		# axs[i].bar(x_axis, y_axis, width= color=tableau20[i])
		ax.plot(x_axis, y_axis, label=key, linestyle="-", linewidth=2, color=tableau20[i])
		ax.legend(loc="lower left")
		# , bbox_to_anchor=[0, 1], 				ncol=2, shadow=False, fancybox=False)

		# if self.upperbond >0 : axs[i].plot(dataset.index,[upperbond]* len(dataset.index),"--", lw=2, color="red", alpha=0.5)
		# if self.upperbond >0 : axs[i].plot(dataset.index,[lowerbond]* len(dataset.index),"--", lw=2, color="red", alpha=0.5)
		i += 1

	# plt.title(title)
	logging.info("Plotting {}".format(plots))
	logging.info("-----------")

	for type in ['png', 'pdf']:
		fileout_complete = "{}_line.{}".format(fileout, type)
		logging.info(" filename: {}".format(fileout_complete))
		plt.savefig(fileout_complete, bbox_inches="tight")


def plot_bar(dataset, fileout, xlim, ylim):
	logging.info("PLOT BAR")

	tableau20 = defTableu()

	plots = len(dataset.keys())
	logging.info("number of plots: {}".format(plots))
	fig = plt.figure(figsize=(12, 9))
	#fig, axs = plt.subplots(plots, figsize=(12, 9), sharex=True, sharey=True)
	#fig.set_size_inches(12, 12)
	width = 0.35
	#colors = [tableau20[0], tableau20[2], tableau20[4]]

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
		#ax.get_xaxis().tick_bottom()
		#ax.get_yaxis().tick_left()
		#ax.set_xticklabels(x_axis, rotation='vertical')
		#ax.set_title(key)
		ax.set_ylabel("Bandwidth (Mbits/sec)")
		if i == plots:
			ax.set_xlabel("Running time (seconds)")
		if xlim is not None:
			ax.set_xlim([0, xlim])

		if ylim is not None:
			ax.set_ylim([0.0, ylim])
		#axs[i].bar(x_axis, y_axis, width= color=tableau20[i])
		ax.bar(x_axis, y_axis, label=get_key(key), color=tableau20[(i-1)*2%20]) #, width=.1, color=tableau20[i])
		ax.legend(loc="lower left", framealpha=1.0)
			#, bbox_to_anchor=[0, 1], 				ncol=2, shadow=False, fancybox=False)

		# if self.upperbond >0 : axs[i].plot(dataset.index,[upperbond]* len(dataset.index),"--", lw=2, color="red", alpha=0.5)
		# if self.upperbond >0 : axs[i].plot(dataset.index,[lowerbond]* len(dataset.index),"--", lw=2, color="red", alpha=0.5)
		i += 1

	# plt.title(title)
	logging.info("Plotting {}".format(plots))
	logging.info("-----------")

	for type in ['png', 'pdf']:
		fileout_complete = "{}_bar.{}".format(fileout, type)
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

	help_msg = "x axys Experiment length (secs) "
	parser.add_argument("--xlim", "-x", help=help_msg, default=X_LIM, type=int)

	help_msg = "y axys Bandwidth (Mbits/sec)"
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
			logging.info("cmd         : {}".format(cmd))
			result_process = subprocess.getoutput(cmd)
			result_data = result_process.split("\n")
			data_set[filename] = result_data

			# cmd = """awk -F'[ -]+' '/sec/{print $1,$4,$5,$9}' %s""" % filename
			# logging.info("cmd         : {}".format(cmd))
			# result_process = subprocess.getoutput(cmd)
			# result_data = result_process.split("\n")
			# data_set[filename] = result_data
			print("")

		logging.info("Plotting")
		logging.info("-------------")
		#plot_line(data_set, args.out, args.xlim, args.ylim)
		plot_bar(data_set, args.out, args.xlim, args.ylim)

if __name__ == '__main__':
	sys.exit(main())