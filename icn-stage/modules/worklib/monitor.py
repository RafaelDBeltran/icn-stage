import psutil as psu
import pandas as pd
from datetime import datetime
import time
import os

class Monitor:

    def __init__(self, PROCESS_SEARCH = None, PATH = './'):
        
        self.PROCESS_SEARCH = PROCESS_SEARCH
        self.PATH = PATH
        # self.UPDATE_TIME = UPDATE_TIME
        # self.header_controller = False
   
    def __del__(self):
        #print('Experiment file termined')
        pass
    
    def run_monitor(self):
        try:

            self.data = []

            for process in psu.process_iter():
                with process.oneshot():
                    self.data.append({
                    'PID': self.get_pid(process),
                    'Name': self.get_process_name(process),
                    'Create_time': self.get_time(process),
                    'Cores': self.get_cpu_usage(process)[0],
                    'Cpu_usage': self.get_cpu_usage(process)[1],
                    'Status': self.get_process_status(process),
                    'Priority': self.get_process_piority(process),
                    'Memory_usage': self.get_memory_use(process),
                    'Read_bytes': self.bytes_behavior(process)[0],
                    'Write_Bytes': self.bytes_behavior(process)[1],
                    'Threads_number': self.get_threads(process),
                    'Command': self.get_command(process)
                    })

            df = pd.DataFrame(self.data)

            df['Memory_usage'] = df['Memory_usage'].apply(self.get_size)
            df['Write_Bytes'] = df['Write_Bytes'].apply(self.get_size)
            df['Read_bytes'] = df['Read_bytes'].apply(self.get_size)


            df2 = df[df.PID == self.PROCESS_SEARCH]

            # os.system("clear")
            df2.to_csv (self.PATH, header=False, mode='a+')
        
        except:
            print('System exit (CTRL+C)')
            pass

    def get_pid(self, process):
        try:
            return process.pid
        except psu.AccessDenied:
            return 0

    def get_time(self, process):
        try:
            now = datetime.now()
            return now.strftime("%H:%M:%S")
        except OSError:
            print('Error on {}'.format(self.get_time.__name__))

    def get_cpu_usage(self, process):
        try:
            return len(process.cpu_affinity()), process.cpu_percent()
        except psu.AccessDenied:
            return 0, process.cpu_percent()

    def get_process_piority(self, process):
        try:
            return int(process.nice())
        except psu.AccessDenied:
            return 0

    def get_memory_use(self, process):
        try:
            return process.memory_full_info().uss
        except psu.AccessDenied:
            return 0

    def bytes_behavior(self, process):
        try:
            io_counters = process.io_counters()
            return io_counters.read_bytes, io_counters.write_bytes
        except psu.AccessDenied:
            #print('Error on {}'.format(bytes_behavior.__name__))
            return 0, 0

    def get_threads(self, process):
        try:
            return process.num_threads()
        except OSError:
            print('Error on {}'.format(self.get_threads.__name__))

    def get_process_name(self, process):
        try:
            return process.name()
        except psu.AccessDenied:
            return "Process not found"

    def get_process_status(self, process):
        try:
            return process.status()
        except psu.AccessDenied:
            return "Status not found"

    def get_size(self, bytes):
        for unit in ['', 'K', 'M', 'G', 'T', 'P']:
            if bytes < 1024:
                return f"{bytes:.2f}{unit}B"
            bytes /= 1024

    def get_command(self, process):
        try:
            return process.cmdline()
        except psu.AccessDenied:
            return 'Not found'
