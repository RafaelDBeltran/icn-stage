#!/bin/bash

sudo apt-get update && sudo apt-get -y upgrade
sudo apt-get -y install git
sudo apt-get --yes install default-jre
sudo timedatectl set-timezone America/Sao_Paulo
sudo timedatectl set-ntp on
#Instasll NDN
#Begin
export SKIPSUDOCHECK=1
export DEFAULT_HOME='/home/vagrant/'

git clone https://github.com/named-data/mini-ndn.git
cd mini-ndn

./install.sh -y
#End


#Instasll NDN
#Begin
cd
git clone https://github.com/named-data/ndn-traffic-generator.git
cd ndn-traffic-generator
./waf configure
./waf
sudo ./waf install
#End

#Install ICN-stage
#Begin
# cd /home/vagrant/
# git clone https://github.com/RafaelDBeltran/icn-stage.git
# cd icn-stage
# git checkout vagrant
# pip install -r requirements.txt

#End