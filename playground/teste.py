
import paramiko
host = "172.17.0.5"

port = 22

username = "icn_user"

password = "icn_user"


command = "ls"


ssh = paramiko.SSHClient()

ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect(host, port, username, password, key_filename='/keys/kub_key.key')


stdin, stdout, stderr = ssh.exec_command(command)

lines = stdout.readlines()

print(lines)