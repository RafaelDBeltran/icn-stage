#!/bin/bash

#ndn-cxx dependences
#sudo apt install build-essential libboost-all-dev libssl-dev libsqlite3-dev pkg-config python-minimal

#ndn-cxx
#git clone https://github.com/named-data/ndn-cxx.git


#sudo rm ${PWD}/ndn-cxx/ndn-cxx/net/impl/linux-if-constants.cpp
#sudo cp linux-if-constants.cpp ${PWD}/ndn-cxx/ndn-cxx/net/impl/

cd ndn-cxx

sudo ./waf configure
sudo ./waf
sudo ./waf install

sudo ldconfig

#cd ..

#NFD dependence

sudo sudo apt install libpcap-dev libsystemd-dev

#NFD

#git clone https://github.com/named-data/NFD.git
cd NFD
git submodule update --init

sudo ./waf configure
sudo ./waf
sudo ./waf install

sudo cp /usr/local/etc/ndn/nfd.conf.sample /usr/local/etc/ndn/nfd.conf

#cd ..

#NLSR dependences

#git clone https://github.com/named-data/ChronoSync

cd ChronoSync
sudo ./waf configure
sudo ./waf
sudo ./waf install

sudo export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${PWD}/ChronoSync/build/libChronoSync.so.0.5.3
sudo echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${PWD}/ChronoSync/build/libChronoSync.so.0.5.3' >> ~/.bashrc
sudo ldconfig
cd ..

#git clone https://github.com/named-data/PSync

cd PSync
sudo ./waf configure
sudo ./waf
sudo ./waf install

sudo export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/PSync/build/libChronoSync.so.0.5.3
sudo echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/PSync/build/libChronoSync.so.0.5.3' >> ~/.bashrc
sudo ldconfig

cd ..

#NLSR install

#git clone https://github.com/named-data/NLSR.git

cd NLSR

sudo ./waf configure
sudo ./waf
sudo ./waf install
sudo mkdir /var/lib/nlsr/

cd ..

#git clone https://github.com/named-data/ndn-tools.git

cd ndn-tools

sudo ./waf configure
sudo ./waf
sudo ./waf install

cd ..

#git clone https://github.com/named-data/ndn-traffic-generator.git

cd ndn-traffic-generator

sudo ./waf configure
sudo ./waf
sudo ./waf install

cd ..

