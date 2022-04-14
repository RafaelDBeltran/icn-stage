FROM ubuntu:18.04

ENV DEBIAN_FRONTEND noninteractive

WORKDIR /icn

COPY . /icn/

RUN apt-get -y -qq update \
&& apt-get -y -qq --no-install-recommends install git build-essential nano curl vim wget iperf3 traceroute iputils-ping ca-certificates gnupg2 \
&& echo "deb [trusted=yes] https://nfd-nightly-apt.ndn.today/ubuntu bionic main" | tee /etc/apt/sources.list.d/nfd-nightly.list \
&& curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
&& echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list \
&& apt-get -y -qq update \
&& apt-get -y -qq --no-install-recommends install -f kubectl ndnsec libndn-cxx-dev nfd ndnchunks  ndnping ndnpeek  ndn-traffic-generator \
&& rm -rf /var/lib/apt/lists/* \
&& cp /etc/ndn/nfd.conf.sample /etc/ndn/nfd.conf \
&& ndnsec-keygen /`whoami` | ndnsec-install-cert - \
&& mkdir -p /etc/ndn/keys /share /logs /workspace \
&& ndnsec-cert-dump -i /`whoami` > default.ndncert \
&& mv default.ndncert /etc/ndn/keys/default.ndncert \
&& setcap -r /usr/bin/nfd || true

RUN set -xe \
    && apt-get -y update \
    && apt-get -y install python3-pip

RUN python3 -m pip install --upgrade pip

RUN python3 -m pip install -r /icn/icn-stage/requirements.txt

RUN apt-get -y update && apt-get -y install tcl openssh-client openssh-server default-jre sudo

RUN useradd -rm -d /home/icn_user -s /bin/bash -g root -G sudo -u 1000 icn_user

RUN  echo 'icn_user:icn_user' | chpasswd

RUN adduser icn_user sudo

RUN sh -c "echo 'icn_user ALL=NOPASSWD: ALL' >> /etc/sudoers"

RUN openssl genrsa -out /icn/keys/id_rsa
RUN openssl rsa -in /icn/keys/id_rsa -pubout > /icn/keys/id_rsa.pub

RUN chmod 777 /icn

RUN chmod -R 777 /icn/keys/

EXPOSE 22
EXPOSE 6363/tcp
EXPOSE 6363/udp

ENTRYPOINT service ssh start && bash