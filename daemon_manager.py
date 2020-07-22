
import psutil
import time
import logging
import os
import subprocess
import sys

from threading import Thread

DEFAULT_SLEEP_SECONDS = 60

class Controller_ICNStage:
    
                    #support thread
                    #threadControl.apply_async(LeaderController('start'))
                    # conectar com todos workers e reconfigurar info.cfg
                    # atualizar a lista através do zookeeper
                    # será possível alterar a lista de diretores com experimento rodando? (eu acho que não)
    
    def __init__(self):
        
        LoopControllerProcess = Thread(target=self.LoopController)                 
        
        try:
            
            if not self.ZookeeperIsRun():    
            
                self.ZookeeperStart()
           
            LoopControllerProcess.start()

            return 0
        
        except:
            
            return -1  
    
    def ControllerDaemon(self,args):
       
        if args=='start':
            
            DaemonControllerProcess =Thread(target=self.LeaderController('start'))
            DaemonControllerProcess.start()

        else:

            DaemonControllerProcess =Thread(target=self.LeaderController('stop'))
            DaemonControllerProcess.start()
            
    
    def ZookeeperStart(self):
        
        try:
            
            logging.info("STARTING ZK")
            subprocess.call("./zookeeper-3.4.14/bin/zkServer.sh start", shell=True)
            logging.info("CONNECTING ZK")
            #controller_client = ControllerClient()
            
            logging.info("CREATING BASIC ZNODES ZK")
            #controller_client.config_create_missing_paths()
            
            if not os.path.isdir("./experiments"):
                logging.info("CREATING EXPERIMENTS FOLDER")
                os.mkdir("./experiments")
            return True
        
        except:
            
            return False
   
    def LeaderController(self,command):
    
        if command=='start':
            print('New leader election.\n(My state) Leader')
            subprocess.call("%s daemon_controller.py restart" % sys.executable, shell=True)
        
        if command=='stop':
            print("New leader election.\n(My state) Follower")
            subprocess.call("%s daemon_controller.py stop" % sys.executable, shell=True)

    def GetStatus(self):
        
        status =os.popen('zookeeper-3.4.14/bin/./zkServer.sh status').read()
        try:
            if status.index('leader'):
                
                return True
            
            else:
                
                return False
        except:
            return False
        
    def LoopController(self):

        while True:
                
            if self.GetStatus():
                print('\n(My Status) LEADER\n')
   
                if not self.CheckDaemonIsRun(): 
                    print('\nDaemonController ativado\n')   
                    self.ControllerDaemon('start')
                   
            else:
                print('\n(MY Status) FOLLOWER\n')
                
                if self.CheckDaemonIsRun():
                    print('\nDaemonController parado\n')
                    self.ControllerDaemon('stop')
                    
                    
            time.sleep(DEFAULT_SLEEP_SECONDS)
                            


    def CheckDaemonIsRun(self):

        process_status = [ proc for proc in psutil.process_iter() if proc.name() == 'daemon_controller.py']
        
        if process_status:
            
            return True
        
        else:
        
            return False
    def ZookeeperIsRun(self):

        process_status = [ proc for proc in psutil.process_iter() if proc.name() == 'zkServer.sh']
        
        if process_status:
            
            return True
        
        else:
        
            return False
        


#  Para utilizar as configurações do modo distribuído do controlador deve-se.
        # importar essa classe
        # instaciar o controlador.
