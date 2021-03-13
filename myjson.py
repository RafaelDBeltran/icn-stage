import json


f = open('settings.json')
data = json.load(f)
JSON_PORT = None
JSON_ADRESS = ''

for i in data['Settings']:
    JSON_PORT = i['ClientPort']

for i in data['Nodes']: 
    JSON_ADRESS += (i['remote_host']+':'+str(JSON_PORT)+',')
    
JSON_ADRESS = JSON_ADRESS[:-1]
print(JSON_ADRESS)
f.close()
    