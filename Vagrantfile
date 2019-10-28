$setup = <<-SCRIPT
sudo apt-get update
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.vm.synced_folder ".", "/abr"
  config.vm.provider "virtualbox" do |v|
    v.gui = false
    v.cpus = 4
    v.memory = 8192
  end
  config.vm.provision "shell", inline: $setup
end
