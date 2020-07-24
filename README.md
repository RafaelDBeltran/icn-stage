# ICN-Stage

ICN-Stage is an open plataform for orchestrating fault-tolerant ICN experimental evaluations.

# To-run
You can run ICN-stage in your machine:
    ./install.sh -qa

We strongly suggest you use a Vagrant + VirtualBox based VM 
    1. Configure you VM (this step may take ~2 hours)
    local-host$ vagrant up 
    2. login in the VM    
    local-host$ vagrant ssh 
    3. run ICN-Stage
    vagrant$ ./icn-stage.py
    4. in another terminal, run mininet
    local-host$ vagrant ssh 
     vagrant$ sudo mn --nat --topo linear,3

    - Apache Zookeeper 3.6.1 (The name of file must be apache-zookeeper-3.6.1).
    - Remove the .example of file config.json.example and edit for you execution env.

In your terminal type:
```sh
$ python new_controller.py
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
