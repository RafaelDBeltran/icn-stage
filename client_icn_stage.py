import socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('0.0.0.0', 8080))
while True:
    
    client.send(str.encode(input("Command:> ")))


client.close()
