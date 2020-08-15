# ICN-Stage

ICN-Stage is an open plataform for orchestrating fault-tolerant ICN experimental evaluations.

# Install
You can install ICN-stage in your machine:
    ```sh
    ./install.sh -s
    ```   

However, we strongly suggest you use a Vagrant + VirtualBox based VM, which contains a Mininet testbed for developing purposes.

1. Configure you VM (this step may take ~2 hours)
    ```sh
    local-host$ vagrant up 
    ```

2. login in the VM    
    ```sh
    local-host$ vagrant ssh 
    ```


# Run CLI
1. You can manually operate ICN-Stage using its CLI. 
    ```sh
    vagrant$ ./icn-stage.py
    ```
    ![ICN-Stage Screenshot](/images/icn-stage-screenshot.png)
    
    
2. In this case, you may want to run the Mininet in another terminal.
    ```sh
    local-host$ vagrant ssh 
    vagrant@ubuntu-bionic:~/icn-stage$ sudo mn --nat --topo linear,3
     ```
     
# Run a play    
1. You can run a play using Mininet
    ```sh
    vagrant@ubuntu-bionic:~/icn-stage$ sudo ./play_mininet_perf.py
    ```
    
2. If you have access to FIBRE, you can run
    ```sh
    vagrant@ubuntu-bionic:~/icn-stage$ sudo ./play_fibre_ndn.py
    ```



# Plot results
1. Plot previosly generated results obtained from play_mininet_perf.py
    ```sh
    vagrant$ python3 plot.py --type iperf --out plot_mn_iperf --xlim 600 --ylim 1.0 results_acm_icn/results_*
    ```
    
    ![Mininet-iperf play](/images/mn_iperf_bar.png)
    ![Mininet-iperf play](/images/mn_iperf_bar.pdf)
    
2. Plot previosly generated results obtained from play_fibre_ndn.py
    ```sh
    vagrant$ python3 plot.py --type ndn --out plot_fibre_ndn --xlim 600 --ylim 10 results_acm_icn/ndn-traffic_results_*
    ```
    ![FIBRE-ndn play](/images/plot_fibre_ndn_bar.png)
    ![FIBRE-ndn play](/images/plot_fibre_ndn_bar.pdf)

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)


   [dill]: <https://github.com/joemccann/dillinger>
   [git-repo-url]: <https://github.com/joemccann/dillinger.git>
   [john gruber]: <http://daringfireball.net>
   [df1]: <http://daringfireball.net/projects/markdown/>
   [markdown-it]: <https://github.com/markdown-it/markdown-it>
   [Ace Editor]: <http://ace.ajax.org>
   [node.js]: <http://nodejs.org>
   [Twitter Bootstrap]: <http://twitter.github.com/bootstrap/>
   [jQuery]: <http://jquery.com>
   [@tjholowaychuk]: <http://twitter.com/tjholowaychuk>
   [express]: <http://expressjs.com>
   [AngularJS]: <http://angularjs.org>
   [Gulp]: <http://gulpjs.com>

   [PlDb]: <https://github.com/joemccann/dillinger/tree/master/plugins/dropbox/README.md>
   [PlGh]: <https://github.com/joemccann/dillinger/tree/master/plugins/github/README.md>
   [PlGd]: <https://github.com/joemccann/dillinger/tree/master/plugins/googledrive/README.md>
   [PlOd]: <https://github.com/joemccann/dillinger/tree/master/plugins/onedrive/README.md>
   [PlMe]: <https://github.com/joemccann/dillinger/tree/master/plugins/medium/README.md>
   [PlGa]: <https://github.com/RahulHP/dillinger/blob/master/plugins/googleanalytics/README.md>
