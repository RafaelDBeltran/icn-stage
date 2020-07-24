# ICN-Stage

ICN-Stage is an open plataform for orchestrating fault-tolerant ICN experimental evaluations.

# To-run
You can run ICN-stage in your machine:
    ```sh
    ./install.sh -s
    ```   

We strongly suggest you use a Vagrant + VirtualBox based VM, which contains a Mininet testbed for the developing purposes.

1. Configure you VM (this step may take ~2 hours)
    ```sh
    local-host$ vagrant up 
    ```

2. login in the VM    
    ```sh
    local-host$ vagrant ssh 
    ```
    
3. run ICN-Stage
    ```sh
    vagrant$ ./icn-stage.py
    ```
    
4. in another terminal, run mininet
    ```sh
    local-host$ vagrant ssh 
     vagrant$ sudo mn --nat --topo linear,3
     ```

    


# IN Building !!!


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
