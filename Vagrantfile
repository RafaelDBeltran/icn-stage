# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"
BOX_IMAGE = "ubuntu/focal64"

directors = {
  "Director1" => { :ip => "192.168.56.110", :cpus => 1, :mem => 1024 },
  "Director2" => { :ip => "192.168.56.111", :cpus => 1, :mem => 1024 },
  "Director3" => { :ip => "192.168.56.112", :cpus => 1, :mem => 1024 }
}

actors = {
   "Actor1" => { :ip => "192.168.56.120", :cpus => 1, :mem => 1024 },
   "Actor2" => { :ip => "192.168.56.121", :cpus => 1, :mem => 1024 },
   "Actor3" => { :ip => "192.168.56.122", :cpus => 1, :mem => 1024 }
}

auxiliar = {
   "Auxiliar1" => { :ip => "192.168.56.130", :cpus => 1, :mem => 1024 }
  # ,"Auxiliar2" => { :ip => "192.168.56.131", :cpus => 1, :mem => 1024 }
#  ,"Director3" => { :ip => "192.168.56.122", :cpus => 1, :mem => 1024 }
}
 
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.synced_folder ".vagrant/machines", "/vagrant_boxes"
  config.vm.synced_folder "results/", "/results"
  config.vm.provision "shell", path: "config_ssh.sh"
  config.vm.provision "shell", path: "config_requirements.sh"
  config.disksize.size = "40GB"

  directors.each_with_index do |(hostname, info), index|
    config.ssh.forward_agent = true
    config.vm.define hostname do |cfg|
      cfg.vm.provider :virtualbox do |vb, override|
        config.vm.box = BOX_IMAGE
        override.vm.network :private_network, ip: "#{info[:ip]}"
        override.vm.hostname = hostname
        vb.name = hostname
        vb.customize ["modifyvm", :id, "--memory", info[:mem], "--cpus", info[:cpus], "--hwvirtex", "on"]
      end # end provider
    end # end config

  end # end directors

  actors.each_with_index do |(hostname, info), index|
    config.vm.define hostname do |cfg|
      cfg.vm.provider :virtualbox do |vb, override|
        config.vm.box = BOX_IMAGE
        override.vm.network :private_network, ip: "#{info[:ip]}"
        override.vm.hostname = hostname
        vb.name = hostname
        vb.customize ["modifyvm", :id, "--memory", info[:mem], "--cpus", info[:cpus], "--hwvirtex", "on"]
      end # end provider
    end # end config

  end # end actors

  auxiliar.each_with_index do |(hostname, info), index|
    config.vm.define hostname do |cfg|
      cfg.vm.provider :virtualbox do |vb, override|
        config.vm.box = BOX_IMAGE
        override.vm.network :private_network, ip: "#{info[:ip]}"
        override.vm.hostname = hostname
        vb.name = hostname
        vb.customize ["modifyvm", :id, "--memory", info[:mem], "--cpus", info[:cpus], "--hwvirtex", "on"]
      end # end provider
    end # end config

  end # end auxiliars





end



