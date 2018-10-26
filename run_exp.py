import argparse
import exp
import os
import subprocess

parser = argparse.ArgumentParser("Main Experiment")
parser.add_argument("--mm-trace",
        type=str,
        default="bw3.mahi",
        help="Mahimahi link trace to use")

args = parser.parse_args()

IP_ADDR = "10.0.0.1"

# One side-effect of using Mahimahi is that you all requests to localhost or 127.0.0.1
# are redirected to within the link shell and can't reach any server running outside.
# To solve this, we could use the host's public IP address, but a simpler option is to
# create a virtual IP address on the public-facing interface.
def setup_virtual_ip():
    ifname = "eth0"
    ret = os.system("sudo ifconfig %s:0 %s > /dev/null 2>&1" % (ifname, IP_ADDR))
    if ret != 0:
        # if eth0 is not available check for an interface that is
        ifname = subprocess.check_output("ifconfig -a | sed 's/[ \t].*//;/^\(lo\|\)$/d' | head -n 1", shell=True)
        ifname = ifname.rstrip()
        print('Interface found: %s' % ifname)
        ret = os.system('sudo ifconfig %s:0 %s ' % (ifname, IP_ADDR))
        assert ret == 0
    return ifname

def teardown_virtual_ip(ifname):
    os.system("sudo ifconfig %s:0 down" % ifname)


ifname = setup_virtual_ip()
exp.start_all(args.mm_trace, IP_ADDR)
teardown_virtual_ip(ifname)

