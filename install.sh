sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python-pip
sudo pip install numpy absl-py pyvirtualdisplay requests python-tk matplotlib
sudo apt-get install -y xfce4 virtualbox-guest-dkms virtualbox-guest-utils virtualbox-guest-x11

# Download the video.
cd /abr/real/data/videos/ && curl -O http://6829fa18.csail.mit.edu:8080/BigBuckBunny.tar.gz
cd /abr/real/data/videos/ && tar -xzf BigBuckBunny.tar.gz
cd /abr/real/data/videos/ && rm BigBuckBunny.tar.gz

# Download the traces using the following lines of code.
cd /abr/network/traces/
curl -O http://6829fa18.csail.mit.edu:8080/traces.tar.gz
tar -xzf traces.tar.gz
rm traces.tar.gz
mv /abr/network/traces/traces/* ./
rm -r /abr/network/traces/traces
