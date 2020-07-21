
import psutil
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
        




def main():
    # arguments
    parser = argparse.ArgumentParser(description='Manager tool for the EasyExp Controller')

    help_msg = "logging level (INFO=%d DEBUG=%d)" % (logging.INFO, logging.DEBUG)
    parser.add_argument("--log", "-l", help=help_msg, default=logging.INFO, type=int)

    cmd_choices = ['restart', 'status', 'install', 'start', 'stop', 'test-tcp', 'test-ndn', 'test-hicn', 'w']
    parser.add_argument('cmd', choices=cmd_choices)

    # parser.print_help()

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
    logging.info("\t command option: %s" % args.cmd)
    logging.info("")

    # process input parameters
    if args.cmd == "status":
        #zookeeper_status()
        x = ControllerClient()
        for worker in sorted(x.worker_get_all(), key=lambda x: x.hostname):
            print(worker)
    elif args.cmd == "restart":
        zookeeper_restart()
    elif args.cmd == "install":
        zookeeper_install()
    elif args.cmd == "start":
        Controller_ICNStage()
    elif args.cmd == "stop":
        zookeeper_stop()
    elif args.cmd == "test-tcp":
        test_tcp()
    elif args.cmd == "test-ndn":
        test_ndn()
    else:
        logging.error("command is not valid: %s" % args.cmd)
