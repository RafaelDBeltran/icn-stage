# ICN-Stage

ICN-Stage is an open plataform for orchestrating fault-tolerant ICN experimental evaluations.

# Install
You can install ICN-stage in your machine:
    ```sh
    ./install.sh -s
    ```   

However, we strongly suggest you use a Vagrant + VirtualBox based VM, which contains a Mininet testbed for the developing purposes.

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
    vagrant$ python3 plot.py --out mn_iperf --xlim 600 results/acm_icm/results_*
    ```
    
2. Plot previosly generated results obtained from play_fibre_ndn.py
    ```sh
    vagrant$ python3 plot.py --out mn_iperf --xlim 600 results/acm_icm/ndn-traffic_results_*
    ```


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
