#!/bin/bash
# -*- Mode:bash; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#sudo timedatectl set-timezone America/Sao_Paulo

# This script is (heavily) based on the Mini-NDN's install.sh script
# please consult the original project (https://github.com/named-data/mini-ndn)
# for licence, authors and further information

test -e /etc/debian_version && DIST="Debian"
grep Ubuntu /etc/lsb-release &> /dev/null && DIST="Ubuntu"

if [[ $DIST == Ubuntu || $DIST == Debian ]]; then
    update='sudo apt-get update'
    install='sudo apt-get -y install'
    remove='sudo apt-get -y remove'
    pkginst='sudo dpkg -i'
    # Prereqs for this script
    if ! which lsb_release &> /dev/null; then
        $install lsb-release
    fi
fi

#TODO#
test -e /etc/fedora-release && DIST="Fedora"
if [[ $DIST == Fedora ]]; then
    update='sudo yum update'
    install='sudo yum -y install'
    remove='sudo yum -y erase'
    pkginst='sudo rpm -ivh'
    # Prereqs for this script
    if ! which lsb_release &> /dev/null; then
        $install redhat-lsb-core
    fi
fi

NDN_SRC="ndn-src"

NDN_GITHUB="https://github.com/named-data"

NDN_CXX_VERSION="master"
NFD_VERSION="master"
PSYNC_VERSION="master"
CHRONOSYNC_VERSION="master"
NLSR_VERSION="master"
NDN_TOOLS_VERSION="master"

if [ $SUDO_USER ]; then
    REAL_USER=$SUDO_USER
else
    REAL_USER=$(whoami)
fi

function patchDummy {
    git -C $NDN_SRC/ndn-cxx apply $(pwd)/patches/ndn-cxx-dummy-keychain-from-ndnsim.patch
    if [[ "$?" -ne 0 ]]; then
        echo "Patch might already be applied"
    fi
}

function quiet_install {
    if [[ $DIST == Ubuntu || $DIST == Debian ]]; then
        update='sudo DEBIAN_FRONTEND=noninteractive apt-get update'
        install='sudo DEBIAN_FRONTEND=noninteractive apt-get -y install'
        remove='sudo DEBIAN_FRONTEND=noninteractive apt-get -y remove'

        echo "wireshark-common wireshark-common/install-setuid boolean false" | sudo debconf-set-selections
    fi
}

function ndn_install {
    mkdir -p $NDN_SRC
    name=$1
    version=$2
    wafOptions=$3

    if [[ $version == "master" ]]; then
        if [[ -d "$NDN_SRC/$name" ]]; then
            pushd $NDN_SRC/$name
            git checkout master
        else
            git clone --depth 1 $NDN_GITHUB/$name $NDN_SRC/$name
            pushd $NDN_SRC/$name
        fi
    else
        if [[ -d $NDN_SRC/$name ]]; then
            pushd $NDN_SRC/$name
            if [[ $(git rev-parse --is-shallow-repository) == "true" ]]; then
                git fetch --unshallow
                git fetch --all
            fi
        else
            git clone $NDN_GITHUB/$name $NDN_SRC/$name
            pushd $NDN_SRC/$name
        fi
        git checkout $version -b version-$version || git checkout version-$version
    fi

    # User must use the same python version as root to use ./waf outside of this script
    sudo -E -u $REAL_USER ./waf configure $wafOptions
    sudo -E -u $REAL_USER ./waf && sudo ./waf install && sudo ldconfig
    popd
}


function ndn {
    if [[ updated != true ]]; then
        $update
        updated="true"
    fi

    if [[ $DIST == Ubuntu || $DIST == Debian ]]; then
        $install git libsqlite3-dev libboost-all-dev make g++ libssl-dev libpcap-dev pkg-config python-pip
    fi

    if [[ $DIST == Fedora ]]; then
        $install gcc-c++ sqlite-devel boost-devel openssl-devel libpcap-devel python-pip
    fi

    ndn_install ndn-cxx $NDN_CXX_VERSION
    ndn_install NFD $NFD_VERSION --without-websocket
    ndn_install PSync $PSYNC_VERSION --with-examples
    ndn_install ChronoSync $CHRONOSYNC_VERSION
    ndn_install NLSR $NLSR_VERSION
    ndn_install ndn-tools $NDN_TOOLS_VERSION
    infoedit
}

function mininet {
    if [[ updated != true ]]; then
        $update
        updated="true"
    fi

    if [[ $pysetup != true ]]; then
        pysetup="true"
    fi

    git clone --depth 1 https://github.com/mininet/mininet
    pushd mininet
    sudo ./util/install.sh -nv
    popd
}

function icn-stage {
    if [[ updated != true ]]; then
        $update
        updated="true"
    fi

    if [[ $pysetup != true ]]; then
        pysetup="true"
    fi

    #pushd icn-stage
	  $install python3-pip moreutils
	  pip3 install --upgrade pip
  	pip3 install -r requirements.txt
  	# cp settings_actors_vagrant.json.example settings_actors.json
  	# cp settings_actors_fibre.json.example settings_actors.json
	  cp config.json.example config.json
	  cp settings.json.example settings.json
	  # cp settings_director_local.json.example settings_director.json
	  # cp settings_director_ensemble.json.example settings_director.json
	  #TODO replace with something as $ ./install_director.py vagrant-box
	  if [ ! -d "./apache-zookeeper-3.6.2" ]; then
	    wget http://mirror.nbtelecom.com.br/apache/zookeeper/zookeeper-3.6.2/apache-zookeeper-3.6.2-bin.tar.gz
	    tar zxf apache-zookeeper-3.6.2-bin.tar.gz
	    mv apache-zookeeper-3.6.2-bin apache-zookeeper-3.6.2
	    rm -f apache-zookeeper-3.6.2-bin.tar.gz
	  fi
	  #ls -s apache-zookeeper-3.6.2-bin zookeeper

    #popd
}

function infoedit {
    git clone --depth 1 https://github.com/NDN-Routing/infoedit.git $NDN_SRC/infoedit
    pushd $NDN_SRC/infoedit
    rm infoedit
    sudo make install
    popd
}

function minindn {
    #old_dir=`pwd`
    #cd ~
    git clone https://github.com/named-data/mini-ndn
    pushd mini-ndn

    $install libigraph0-dev tshark
    sudo pip install -r requirements.txt

    if [[ updated != true ]]; then
        if [ ! -d "build" ]; then
            $update
            updated="true"
        fi
    fi

    if [[ $pysetup != true ]]; then
        $install python-setuptools
        pysetup="true"
    fi
    install_dir="/usr/local/etc/mini-ndn/"

    sudo mkdir -p "$install_dir"
    sudo cp topologies/default-topology.conf "$install_dir"
    sudo cp topologies/minindn.caida.conf "$install_dir"
    sudo cp topologies/minindn.ucla.conf "$install_dir"
    sudo cp topologies/minindn.testbed.conf "$install_dir"
    sudo cp topologies/current-testbed.conf "$install_dir"
    sudo cp topologies/geo_hyperbolic_test.conf "$install_dir"
    sudo cp topologies/geant.conf "$install_dir"
    sudo python setup.py develop

    popd

    #cd $old_dir
}

function ndn_cpp {
    if [[ updated != true ]]; then
        $update
        updated="true"
    fi

    if [[ $DIST == Ubuntu || $DIST == Debian ]]; then
        $install git build-essential libssl-dev libsqlite3-dev libboost-all-dev libprotobuf-dev protobuf-compiler
    fi

    if [[ $DIST == Fedora ]]; then
        printf '\nNDN-CPP does not support Fedora yet.\n'
        return
    fi

    git clone --depth 1 $NDN_GITHUB/ndn-cpp $NDN_SRC/ndn-cpp
    pushd $NDN_SRC/ndn-cpp
    ./configure
    proc=$(nproc)
    make -j$proc
    sudo make install
    sudo ldconfig
    popd
}

function pyNDN {
    if [[ updated != true ]]; then
        $update
        updated="true"
    fi

    if [[ $DIST == Ubuntu || $DIST == Debian ]]; then
        $install git build-essential libssl-dev libffi-dev python-dev python-pip
    fi

    if [[ $DIST == Fedora ]]; then
        printf '\nPyNDN does not support Fedora yet.\n'
        return
    fi

    sudo pip install cryptography trollius protobuf pytest mock
    git clone --depth 1 $NDN_GITHUB/PyNDN2 $NDN_SRC/PyNDN2
    pushd $NDN_SRC/PyNDN2
    # Update the user's PYTHONPATH.
    echo "export PYTHONPATH=\$PYTHONPATH:`pwd`/python" >> ~/.bashrc
    # Also update root's PYTHONPATH in case of running under sudo.
    echo "export PYTHONPATH=\$PYTHONPATH:`pwd`/python" | sudo tee -a /root/.bashrc > /dev/null
    popd
}

function ndn_js {
    if [[ updated != true ]]; then
        $update
        updated="true"
    fi

    if [[ $DIST == Ubuntu || $DIST == Debian ]]; then
        $install git nodejs npm
    fi

    if [[ $DIST == Fedora ]]; then
        printf '\nNDN-JS does not support Fedora yet.\n'
        return
    fi

    sudo ln -fs /usr/bin/nodejs /usr/bin/node
    sudo npm install -g mocha
    sudo npm install rsa-keygen sqlite3
    git clone --depth 1 $NDN_GITHUB/ndn-js $NDN_SRC/ndn-js
}

function jNDN {
    if [[ updated != true ]]; then
        $update
        updated="true"
    fi

    if [[ $DIST == Ubuntu || $DIST == Debian ]]; then
        $install git openjdk-8-jdk maven
    fi

    if [[ $DIST == Fedora ]]; then
        printf '\nNDN-JS does not support Fedora yet.\n'
        return
    fi

    git clone --depth 1 $NDN_GITHUB/jndn $NDN_SRC/jndn
    pushd $NDN_SRC/jndn
    mvn install
    popd
}

function commonClientLibraries {
    ndn_cpp
    pyNDN
    ndn_js
    jNDN
}

function buildDocumentation {
    sphinxInstalled=$(pip show sphinx | wc -l)
    sphinxRtdInstalled=$(pip show sphinx_rtd_theme | wc -l)
    if [[ $sphinxInstalled -eq "0" ]]; then
        pip install sphinx
    fi

    if [[ $sphinxRtdInstalled -eq "0" ]]; then
        pip install sphinx_rtd_theme
    fi
    cd docs
    make clean
    make html
}

function usage {
    printf '\nUsage: %s [-a]\n\n' $(basename $0) >&2

    printf 'options:\n' >&2
    printf -- ' -a: install all the required dependencies\n' >&2
    printf -- ' -c: install Common Client Libraries\n' >&2
    printf -- ' -d: build documentation\n' >&2
    printf -- ' -h: print this (H)elp message\n' >&2
    printf -- ' -i: install mini-ndn\n' >&2
    printf -- ' -m: install mininet and dependencies\n' >&2
    printf -- ' -n: install NDN dependencies of mini-ndn including infoedit\n' >&2
    printf -- ' -p: patch ndn-cxx with dummy key chain\n' >&2
    printf -- ' -q: quiet install (must be specified first)\n' >&2
    printf -- ' -s: install icn-stage\n' >&2
    exit 2
}

if [[ $# -eq 0 ]]; then
    usage
else
    while getopts 'acdhimnpqs' OPTION
    do
        case $OPTION in
        a)
        ndn
        mininet
        commonClientLibraries
        icn-stage
        break
        ;;
        c)    commonClientLibraries;;
        d)    buildDocumentation;;
        h)    usage;;
        i)    minindn;;
        m)    mininet;;
        n)    ndn;;
        p)    patchDummy;;
        q)    quiet_install;;
        s)    icn-stage;;
        ?)    usage;;
        esac
    done
    shift $(($OPTIND - 1))
fi
