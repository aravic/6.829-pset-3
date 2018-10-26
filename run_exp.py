import argparse
import exp
import os
import subprocess

parser = argparse.ArgumentParser("Main Experiment")
parser.add_argument("--mm-trace",
        type=str,
        default="bw3.mahi",
        help="Mahimahi link trace to use")
parser.add_argument("--headless",
        dest="headless",
        action="store_true",
        help="Whether to run in a headless chrome browser")
parser.add_argument("--ip-addr",
        type=str,
        default="10.0.0.1",
        help="Virtual interface to run over (for Mahimahi)")
args = parser.parse_args()

# One side-effect of using Mahimahi is that you all requests to localhost or 127.0.0.1
# are redirected to within the link shell and can't reach any server running outside.
# To solve this, we could use the host's public IP address, but a simpler option is to
# create a virtual IP address on the public-facing interface.
def setup_virtual_ip(ip_addr):
    ifname = "eth0"
    ret = os.system("sudo ifconfig %s:0 %s > /dev/null 2>&1" % (ifname, ip_addr))
    if ret != 0:
        # if eth0 is not available check for an interface that is
        ifname = subprocess.check_output("ifconfig -a | sed 's/[ \t].*//;/^\(lo\|\)$/d' | head -n 1", shell=True)
        ifname = ifname.rstrip()
        print('Interface found: %s' % ifname)
        ret = os.system('sudo ifconfig %s:0 %s ' % (ifname, ip_addr))
        assert ret == 0
    return ifname

def teardown_virtual_ip(ifname):
    os.system("sudo ifconfig %s:0 down" % ifname)


ifname = setup_virtual_ip(args.ip_addr)
exp.start_all(args)
teardown_virtual_ip(ifname)

