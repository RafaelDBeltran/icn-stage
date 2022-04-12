# ICN-Stage

ICN-stage é uma plataforma aberta para orquestração e tolerância a falhas para avaliação experimental de cenas ICN.

# Download
```sh
git clone git@github.com:RafaelDBeltran/icn-stage.git
```

```sh
cd icn-stage; git checkout kubernetes
```
    
# Install 
Kubernetes
Python
(Zookeeper não é necessário pois é instalado e configurado automaticamente)

# Deploy
0. Executar o minikube 
```sh
minikube start
```

1. Configurar o ambiente kubernets
```sh
python3 setup_kubernets.py local
```

# Run

2. Acessar algum diretor
```sh
kubectl exec --stdin --tty director1 -- /bin/bash
```

3. Executar a interface por linha de comando do icn-stage
```sh
python3 icn-stage/cli.py
```

4. Na interface, listar comandos
```sh
icn-stage>> help
```

----

1. Para fazer o deploy dos pods, deve-se executar o comando abaixo para cada pod.
   Para criar um novo pod, sugere-se copiar o arquivo de exemplo e editar a chave "name".
   Obs1: o nome dos pods deve ser sempre em letra minúscula.
   Obs2: crie um chamado de controlador.
   
   Para deploy do director1, execute:
    ```sh
    kubectl apply -f deployment_director1.yaml_
    ```
    
    Para deploy dos três diretores, execute:
    ```sh
      for i in 1 2 3; do kubectl apply -f deployment_director$i.yaml_; done
    ```
    
    Para deploy dos três atores, execute:
    ```sh
      for i in 1 2 3; do kubectl apply -f deployment_actor$i.yaml_; done
    ```
    
2. Execute o python_kube.py para criar os arquivos de configurações e enviar para os respectivos pods.

   ```sh
   python3 python_kube.py
   ```
3. Acesse o Director1 

   ```sh
   kubectl exec --stdin --tty director1 -- /bin/bash
   ```
   No diretor, execute o icn-stage
    ```sh
    cd icn-stage; python3 icn-stage.py
   ```

   
4. Acesse o controlador onde vamos interagir com o icn-stage e execute o terminal do icn-stage.

   ```sh
   local-host:~/icn-stage$ kubectl exec --stdin --tty controlador -- /bin/bash

   root@controlador:/icn/playground# python3 client_icn_stage.py
   ```

# Stop


1.  
   Para parar director1, execute:
    ```sh
    kubectl delete pod director
    ```
    
    Para parar três diretores, execute:
    ```sh
      for i in 1 2 3; do kubectl delete pod director$i; done
    ```
    
    Para parar três atores, execute:
    ```sh
      for i in 1 2 3; do kubectl delete pod actor$i; done
    ```
    Para parar todos os pods, execute:
    ```sh
    kubectl delete pod --all
    ```
2. Parar o minikube 
```sh
minikube stop
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
