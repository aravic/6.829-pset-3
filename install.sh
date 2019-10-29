sudo DEBIAN_FRONTEND=noninteractive apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

sudo apt-get install -y python-pip
sudo pip install numpy absl-py matplotlib

sudo apt-get install -y xfce4 virtualbox-guest-dkms virtualbox-guest-utils virtualbox-guest-x11

# Download the traces using the following lines of code.
cd /abr/network/traces/
curl -O http://6829fa18.csail.mit.edu:8080/traces.tar.gz
tar -xzf traces.tar.gz
rm traces.tar.gz
mv /abr/network/traces/traces/* ./
rm -r /abr/network/traces/traces
