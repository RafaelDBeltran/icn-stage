FROM ubuntu

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /icn

COPY . /icn/

RUN apt-get -y update && apt-get -y install tcl python3-pip git openssh-client openssh-server iputils-ping default-jre nano sudo \
&& pip install -r /icn/icn-stage/requirements.txt

RUN useradd -rm -d /home/icn_user -s /bin/bash -g root -G sudo -u 1000 icn_user

RUN  echo 'icn_user:icn_user' | chpasswd

RUN adduser icn_user sudo

RUN sh -c "echo 'icn_user ALL=NOPASSWD: ALL' >> /etc/sudoers"

RUN openssl genrsa -out /icn/keys/id_rsa
RUN openssl rsa -in /icn/keys/id_rsa -pubout > /icn/keys/id_rsa.pub

RUN chmod 777 /icn

ENTRYPOINT service ssh start && bash

RUN apt-get -y install --no-install-recommends ca-certificates curl git mawk

RUN git clone https://github.com/named-data/mini-ndn.git && cd mini-ndn/ && ./install.sh -y

RUN git clone https://github.com/named-data/ndn-traffic-generator.git && cd ndn-traffic-generator/ && ./waf configure && ./waf && ./waf install

EXPOSE 22

CMD ["/usr/sbin/sshd","-D"]