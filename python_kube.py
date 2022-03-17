from kubernetes import client, config

# Configs can be set in Configuration class directly or using helper utility

Diretores = []
Atores = []
Auxiliares = []

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
        Diretores.append({i.status.pod_ip: i.metadata.name})
    elif 'actor' in i.metadata.name:
        Atores.append({i.status.pod_ip: i.metadata.name})
    elif 'auxiliar' in i.metadata.name:
        Auxiliares.append({i.status.pod_ip: i.metadata.name})
    else:
        pass
    # print("%s\t%s" % (i.status.pod_ip, i.metadata.name))

print(Diretores)
print(Atores)