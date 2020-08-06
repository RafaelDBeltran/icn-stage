# -*- mode: ruby -*-
# vi: set ft=ruby :

$script = <<SCRIPT
# Create a symlink between host and VM
ln -s /vagrant /home/vagrant/icn-stage

# Check if install.sh is present or someone just copied the Vagrantfile directly
if [[ -f /home/vagrant/icn-stage/install.sh ]]; then
 pushd /home/vagrant/icn-stage
else
  # Remove the symlink
  rm /home/vagrant/icn-stage
  git clone --depth 1 https://github.com/RafaelDBeltran/icn-stage.git
  pushd icn-stage
fi
./install.sh -qa

SCRIPT

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/bionic64"
  config.vm.provision "shell", privileged: false, inline: $script
  config.vm.provider "virtualbox" do |vb|
    vb.name = "icn-stage_box"
    vb.memory = 4096
    vb.cpus = 4
	vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
  end
end

 
Vagrant.configure(2) do |config|
  config.ssh.forward_x11 = true 
end


 