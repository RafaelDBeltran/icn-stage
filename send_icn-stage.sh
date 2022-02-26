#!/bin/bash

vagrant scp ../icn-stage Director1:~/
vagrant scp ../icn-stage Director2:~/
vagrant scp ../icn-stage Director3:~/
vagrant scp ../icn-stage Actor1:~/
vagrant scp ../icn-stage Actor2:~/
vagrant scp ../icn-stage Actor3:~/
vagrant scp ../icn-stage Auxiliar1:~/

vagrant ssh -c "pip install -r /home/vagrant/icn-stage/requirements.txt && sudo pip install -r /home/vagrant/icn-stage/requirements.txt" Director1
vagrant ssh -c "pip install -r /home/vagrant/icn-stage/requirements.txt && sudo pip install -r /home/vagrant/icn-stage/requirements.txt" Director2
vagrant ssh -c "pip install -r /home/vagrant/icn-stage/requirements.txt && sudo pip install -r /home/vagrant/icn-stage/requirements.txt" Director3
vagrant ssh -c "pip install -r /home/vagrant/icn-stage/requirements.txt && sudo pip install -r /home/vagrant/icn-stage/requirements.txt" Actor1
vagrant ssh -c "pip install -r /home/vagrant/icn-stage/requirements.txt && sudo pip install -r /home/vagrant/icn-stage/requirements.txt" Actor2
vagrant ssh -c "pip install -r /home/vagrant/icn-stage/requirements.txt && sudo pip install -r /home/vagrant/icn-stage/requirements.txt" Actor3
vagrant ssh -c "pip install -r /home/vagrant/icn-stage/requirements.txt && sudo pip install -r /home/vagrant/icn-stage/requirements.txt" Auxiliar1

