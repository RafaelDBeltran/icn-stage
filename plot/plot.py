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
import matplotlib.colors as colors
import matplotlib.cm as cmx

import subprocess
import argparse
import logging

TIME_FORMAT = '%Y-%m-%d,%H:%M:%S'
Y_LIM = None
X_LIM = None

DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_OUT_FILE_NAME = "result"
DEFAULT_TYPE = "ndn"
 

key_titles = {}
key_titles["results_fail-OFF_recover-ON"] = "Zero fault"
key_titles["results_fail-ON_recover-ON"] = "One fault; two actors"
key_titles["results_fail-ON_recover-OFF"] = "One fault; one actor"

key_titles["ndn_traffic_Peça_sem_falha"] = "Zero falha"
key_titles["ndn_traffic_Peça_com_falha_e_recuperação"] = "Uma falha; Um reserva"
key_titles["ndn_traffic_Peça_com_falha"] = "Uma falha; Zero reserva"

key_titles["fibre_sem_falha"] = "FIBRE"

def get_key(key):

	for k in key_titles.keys():
		if k in key:
			return key_titles[k]

	return key


def process_sum(data, data_type=DEFAULT_TYPE):

	first_value = None
	results = {}
	result_x = []
	result_y = []

	for line in data:
		# it's [SUM] line cuted by awk
		if "Mbits/sec" in line:
			continue

		try:
			# clock = line.split(" ")[0]
			#
			# # x format: HH:MM:SS example: 00:02:59
			# clock = (int(clock.split(":")[0])*60*60) + (int(clock.split(":")[1])*60) + (int(clock.split(":")[2]))
			# if first_value is None:
			# 	first_value = clock
			# clock -= first_value
			# interval_begin = int(float(line.split(" ")[1]) + clock)
			# interval_end = int(float(line.split(" ")[2]) + clock)
			# value_x = "%03d-%03d" % (interval_begin, interval_end)
			# value_y = float(line.split(" ")[3])

			value_x = line.split(" ")[0]
			# x format: HH:MM:SS example: 00:02:59
			value_x = (int(value_x.split(":")[0]) * 60 * 60) + (int(value_x.split(":")[1]) * 60) + (
				int(value_x.split(":")[2]))
			if first_value is None:
				first_value = value_x

			value_x -= first_value

			value_y = 0.0
			if data_type == "iperf":
				value_y = float(line.split(" ")[1])
			elif data_type == "ndn":
				value_y = 1
			else:
				logging.error("Data type unknown: {}".format(data_type))
				sys.exit(-1)

			if value_x not in results:
				results[value_x] = value_y
			else:
				results[value_x] += value_y
			logging.debug("x:{} y:{} line:'{}'".format(value_x, value_y, line))

		except Exception as e:
			logging.error("Exception while reading line: '{}' exception: {} ".format(line, e))
			continue

	for key in sorted(results.keys()):
		logging.debug("x:{} y:{} ".format(key, results[key]))
		result_x += [key]
		result_y += [results[key]]

	return result_x, result_y


# def process(data, data_type=DEFAULT_TYPE):
# 	first_value = None
# 	result_x = []
# 	result_y = []
# 	for line in data:
# 		# it's [SUM] line
# 		if "Mbits/sec" in line:
# 			continue
#
# 		try:
# 			value_x = line.split(" ")[0]
#
# 			# x format: HH:MM:SS example: 00:02:59
# 			value_x = (int(value_x.split(":")[0])*60*60) + (int(value_x.split(":")[1])*60) + (int(value_x.split(":")[2]))
# 			if first_value is None:
# 				first_value = value_x
#
# 			value_x -= first_value
# 			value_y = 0.0
# 			if data_type == "iperf":
# 				value_y = float(line.split(" ")[1])
# 			elif data_type == "ndn":
# 				value_y = 1
# 			else:
# 				logging.error("Data unknown: {}".format(data_type))
#
# 			logging.debug("{} {} {}".format(line.split(" ")[0], value_x, value_y))
#
# 		except Exception as e:
# 			logging.error("Exception while reading line: {} exception: {} ".format(line, e))
# 			continue
#
# 		result_x += [value_x]
# 		result_y += [value_y]
#
# 	return result_x, result_y


def plot_bar(dataset, fileout, xlim, ylim, data_type):
	logging.info("PLOT BAR")
	plots = len(dataset.keys())

	# full list of color maps
	# https://matplotlib.org/2.0.2/examples/color/colormaps_reference.html
	tab10 = cm = plt.get_cmap('tab10')
	values = range(plots)
	cNorm = colors.Normalize(vmin=0, vmax=9)
	scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=tab10)

	logging.info("number of plots: {}".format(plots))
	if plots == 3:
		plt.rcParams.update({'font.size': 40})
		fig = plt.figure(figsize=(12, 16))
	else:
		plt.rcParams.update({'font.size': 20})
		fig = plt.figure()

	# add a big axis, hide frame invisible
	ax_invis = fig.add_subplot(111, frameon=False)
	fig.subplots_adjust(hspace=.5)

	if data_type == "ndn":
		ax_invis.set_ylabel("Interesses recebidos pelo publicador")
	else:
		ax_invis.set_ylabel("Iperf Server Bandwidth (Mbits/sec)")

	ax_invis.set_xlabel("Tempo de execução (segundos)")

	# hide tick and tick label of the big axes
	ax_invis.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)

	i = 1
	logging.info("Plotting {}".format(plots))
	logging.info("-------------")
	for key in dataset.keys():
		logging.debug("\tkey : {}".format(key))

		# data = dataset[key]
		# logging.debug("data: {}".format(data))
		#x_axis, y_axis = process(data)
		#x_axis, y_axis = process_sum(data)
		x_axis, y_axis = dataset[key]
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
		#ax.set_ylabel("BW (Mbits/sec)")
		# if i == plots:
		# 	ax.set_xlabel("Running time (seconds)")

		if ylim == 1:
			ax.set_yticks([1.0, 0.5, 0.0])
		elif ylim == 10:
			ax.set_yticks([10, 5, 0])

		if xlim is not None:
			ax.set_xlim([0, xlim])

		if ylim is not None:
			ax.set_ylim([0.0, ylim])

		colorVal = scalarMap.to_rgba(values[i-1])
		ax.bar(x_axis, y_axis, label=get_key(key), color=colorVal)
		#ax.bar(x_axis, y_axis, label=get_key(key), color=tableau20[(i-1)*2%20]) #, width=.1, color=tableau20[i])
		ax.legend(loc="lower left", framealpha=1.0)
		i += 1

	logging.info("Saving")
	logging.info("------")
	for type in ['png', 'pdf']:
		fileout_complete = "{}_bar.{}".format(fileout, type)
		logging.info("\tfilename: {}".format(fileout_complete))
		plt.savefig(fileout_complete, bbox_inches="tight")


def main():
	parser = argparse.ArgumentParser(description='ICN-Stage experiments plotter')

	help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
	parser.add_argument("--log", "-l", help=help_msg, default=DEFAULT_LOG_LEVEL, type=int)

	help_msg = "outputfile (default={})".format(DEFAULT_OUT_FILE_NAME)
	parser.add_argument("--out", "-o", help=help_msg, default=DEFAULT_OUT_FILE_NAME, type=str)

	help_msg = "input_file_1 input_file_2 ... input_file_N "
	parser.add_argument('files', type=str, help=help_msg, nargs=argparse.ONE_OR_MORE)

	help_msg = "x axis Experiment length (secs) "
	parser.add_argument("--xlim", "-x", help=help_msg, default=X_LIM, type=int)

	help_msg = "y axis Bandwidth (Mbits/sec)"
	parser.add_argument("--ylim", "-y", help=help_msg, default=Y_LIM, type=float)

	help_msg = "type [iperf|ndn]"
	parser.add_argument("--type", "-t", help=help_msg, default=DEFAULT_TYPE, type=str)

	# read arguments from the command line
	args = parser.parse_args()

	# setup the logging facility
	if args.log == logging.DEBUG:
		logging.basicConfig(format='%(asctime)s %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
							datefmt=TIME_FORMAT, level=args.log)

	else:
		logging.basicConfig(format='%(asctime)s %(message)s',
							datefmt=TIME_FORMAT, level=args.log)

	logging.info("")
	logging.info("INPUT")
	logging.info("---------------------")
	logging.info("\t logging level : {}".format(args.log))
	logging.info("\t xlim          : {}".format(args.xlim))
	logging.info("\t ylim          : {}".format(args.ylim))
	logging.info("\t out           : {}".format(args.out))
	logging.info("\t type          : {}".format(args.type))
	logging.info("\t files         : {}".format(args.files))
	logging.info("")

	logging.info("Reading files")
	logging.info("-------------")
	print("")

	data_set = {}
	for filename in args.files:

		logging.info("file name   : {}".format(filename))
		cmd = """awk -F'[ -]+' '/sec/{print $1,$9}' %s""" % filename

		if args.type == "ndn":
			cmd = """awk  '/Interest received/{print $2,$7}' %s""" % filename

		logging.info("cmd         : {}".format(cmd))
		result_process = subprocess.getoutput(cmd)
		result_data = result_process.split("\n")
		logging.info("\tprocessing...")
		x_axis, y_axis = process_sum(result_data, args.type)
		data_set[filename] = (x_axis, y_axis)
		print("")

	logging.info("Plotting")
	logging.info("--------")
	plot_bar(data_set, args.out, args.xlim, args.ylim, args.type)


if __name__ == '__main__':
	sys.exit(main())