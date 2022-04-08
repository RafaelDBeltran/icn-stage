# ICN-Stage

ICN-stage é uma plataforma aberta para orquestração e tolerância a falhas para avaliação experimental de cenas ICN.

# Download do Projeto

    ```sh
    local-host:~/$ git clone git@github.com:RafaelDBeltran/icn-stage.git
    local-host:~/$ cd icn-stage/
    local-host:~/icn-stage$ git checkout kubernetes
    ```

# Deploy
0. Executar o minikube 
```sh
minikube start
```

1. Para fazer o deploy dos pods, deve-se executar o comando abaixo para cada pod.
   Para criar um novo pod, sugere-se copiar o arquivo de exemplo e editar a chave "name".
   Obs1: o nome dos pods deve ser sempre em letra minúscula.
   Obs2: crie um chamado de controlador.
   
   Para deploy do director1, execute:
    ```sh
    local-host:~/icn-stage$ kubectl apply -f deployment_director1.yaml_
    ```
2. Execute o python_kube. Ele irá criar o arquivo de configurações e enviar para os pods.

   ```sh
   local-host:~/icn-stage$ python3 python_kube.py
   ```
3. Acesse o Director1 com o comando abaixo e execute o icn-stage

   ```sh
   local-host:~/icn-stage$ kubectl exec --stdin --tty director1 -- /bin/bash

   root@director1:/icn/icn-stage# python3 icn-stage.py
   ```
4. Acesse o controlador onde vamos interagir com o icn-stage e execute o terminal do icn-stage.

   ```sh
   local-host:~/icn-stage$ kubectl exec --stdin --tty controlador -- /bin/bash

   root@controlador:/icn/playground# python3 client_icn_stage.py
   ```

## Comandos no ICN-stage
Para iniciar o ensemble
```sh
Command[172.17.0.4]> ensemble-start
```
Iniciar conexão com zookeeper
```sh
Command[172.17.0.3]> start
```
Adicionar atores
```sh
Command[172.17.0.3]> addactors
```
Realizar teste com cliente-servidor TCP
```sh
Command[172.17.0.3]> test
```

Os logs podem ser observados no arquivo /tmp/daemon_director_ensemble_1.stderr do diretor principal.

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
