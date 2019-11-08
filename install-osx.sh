# We assume you already have python and pip installed

pip install numpy matplotlib absl-py urllib2

# Download traces
cd ./network/traces/
curl -O http://6829fa18.csail.mit.edu:8080/traces.tar.gz
tar -xzf traces.tar.gz
rm traces.tar.gz
echo `pwd`
mv traces/* ./
rm -r traces
