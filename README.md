# ICN-Stage

ICN-Stage is an open plataform for orchestrating fault-tolerant ICN experimental evaluations.

# Install
Esse branch é focado num ambiente contido gerado pelo vagrant. 

1. Configurar VM's (esse procedimento pode levar ~1 hora)
    ```sh
    local-host:~/icn-stage$ vagrant up 
    ```

2. Enviar icn-stage e instalar dependencias    
    ```sh
    local-host:~/icn-stage$ vagrant plugin install vagrant-scp
    local-host:~/icn-stage$ ./send_icn-stage.sh
    ```
# Execução
1. Executar icn-stage
    ```sh
    local-host:~/icn-stage$ vagrant ssh Director1
    ```

    ```python
    vagrant@Director1:~/$ python3 icn-stage/icn-stage.py
    ```

2. Enviar comandos a partir do Host
    ```python
    local-host:~/icn-stage$ python3 client_icn_stage.py
    ```
## Instruções de Uso
1. Iniciar Ensemble
    ```sh
    Command[192.168.56.111]> ensemble-start
    ```

2. Iniciar Daemon Director
    ```sh
    Command[192.168.56.112]> start
    ```
3. Adicionar atores
    ```sh
    Command[192.168.56.112]> addactors
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
