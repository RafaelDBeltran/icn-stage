from kubernetes import client, config
import subprocess

Diretores = {}
Atores = {}
Auxiliares = {}

Diretores_count = 1
Atores_count = 1
Auxiliares_count = 1

user = 'icn_user'
password = 'icn_user'

config.load_kube_config()

v1 = client.CoreV1Api()

ret = v1.list_pod_for_all_namespaces(watch=False)
for i in ret.items:
    if 'director' in i.metadata.name:
        Diretores[i.metadata.name] = i.status.pod_ip
    elif 'actor' in i.metadata.name:
        Atores[i.metadata.name] = i.status.pod_ip
    elif 'auxiliar' in i.metadata.name:
        Auxiliares[i.metadata.name] = i.status.pod_ip
    else:
        pass

# print(Diretores)
# print(Atores)

config = '''{\"zookeeper_adapter\": \"eth0\",\n
"Nodes": [\n
'''

for key, value in Diretores.items():
    if Diretores_count > 1:
        config += ','
    config +=  '{\"remote_id\": \"'+str(Diretores_count)+'\", \"remote_hostname\": \"'+value+'\",\"remote_username\": \"icn_user\",\"remote_password\": \"icn_user\",\"remote_pkey_path\": \"/icn/keys/id_rsa\",\"Function": \"'+key+'\"} \n'
    Diretores_count += 1
config += '''\n],
\"workers\":[
'''

for key, value in Atores.items():
    if Atores_count > 1:
        config += ','
    config +=  '{\"actor_id\": \"'+str(Atores_count)+'\", \"remote_hostname\": \"'+value+'\",\"remote_username\": \"icn_user\",\"remote_password\": \"icn_user\",\"remote_pkey_path\": \"/icn/keys/id_rsa\",\"Function": \"'+key+'\"} \n'
    Atores_count += 1
config += '''\n]'''

config += '\n}'
# print(config)
text_file = open("config.json", "w")
text_file.write(config)
text_file.close()

for key, _ in Diretores.items():
    subprocess.run('kubectl cp config.json {}:/icn/icn-stage'.format(key),shell=True)
    subprocess.run('kubectl exec -it {} -- /bin/bash -c "sudo /etc/init.d/ssh start"'.format(key),shell=True)

for key, _ in Atores.items():
    subprocess.run('kubectl exec -it {} -- /bin/bash -c "sudo /etc/init.d/ssh start"'.format(key),shell=True)

subprocess.run('kubectl cp config.json controlador:/icn/playground',shell=True)
subprocess.run('cp config.json playground',shell=True)