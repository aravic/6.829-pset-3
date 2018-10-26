$setup = <<-SCRIPT
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y mahimahi

# mahimahi setup
echo "sudo sysctl -w net.ipv4.ip_forward=1" >> ~/.bashrc

sudo apt-get install -y python-pip
sudo pip install numpy
sudo pip install pyvirtualdisplay

sudo apt-get install -y google-chrome-stable
sudo apt-get install -y xfce4 virtualbox-guest-dkms virtualbox-guest-utils virtualbox-guest-x11
sudo sed -i 's/allowed_users=.*$/allowed_users=anybody/' /etc/X11/Xwrapper.config

cd /abr/server/data/videos && curl -O http://6829fa18.csail.mit.edu:8080/BigBuckBunny.tar.gz
cd /abr/server/data/videos && tar -xzf BigBuckBunny.tar.gz
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.vm.synced_folder ".", "/abr"
  config.vm.provider "virtualbox" do |v|
    v.gui = true
  end
  config.vm.provision "shell", inline: $setup
end