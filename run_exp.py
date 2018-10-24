import sys
import os
import argparse
import subprocess

parser = argparse.ArgumentParser("Main Experiment")
parser.add_argument("--mm-trace",
        type=str,
        default="",
        help="Mahimahi link trace to use")
parser.add_argument("--video",
        type=str,
        default="BigBuckBunny",
        help="Video to watch")

args = parser.parse_args()

IP_ADDR = "10.0.0.1"
VID_SERVER_PORT = 4443

def get_python_cmds(logfile):
    # Start ABR server.
    cmds = []
    cmds.append("python abr_server.py --video=%s > logs/abr_server.log 2>&1 &" % args.video)
    # Start mahimahi tailing server. TODO
    # Start chrome:
    cmds.append("google-chrome --user-data-dir=/tmp/chrome_user_dir --incognito http://%s:%d/videos/%s > logs/chrome.log 2>&1" % (IP_ADDR, VID_SERVER_PORT, args.video))
    return cmds

def mm_cmd():
    mm_log_file = "logs/mm_downlink.log"
    # Put in 1 BDP of buffer, assuming an average of 2 Mbps.
    rtt_ms = 80
    queue = 2 * rtt_ms / 12
    mm_queue_args="packets=%d" % queue
    link_cmd = 'mm-link %s %s --downlink-log=%s --downlink-queue=droptail\
        --downlink-queue-args="%s" <<EOF\n%s\nEOF' % \
        ("bw12.mahi", args.mm_trace, mm_log_file, mm_queue_args,
                '\n'.join(get_python_cmds(mm_log_file)))
    delay_cmd = 'mm-delay %d %s' % (rtt_ms / 2, link_cmd)
    print delay_cmd
    return delay_cmd

def start_video_server():
    proc = subprocess.Popen("python3 video_server.py --host=%s --port=%d > logs/video_server.log 2>&1" % (IP_ADDR, VID_SERVER_PORT),
            stdout=sys.stdout, stderr=sys.stderr, shell=True)
    return proc

def start_mm_cmd():
    proc = subprocess.Popen(mm_cmd(), stdout=sys.stdout, stderr=sys.stderr, shell=True)
    return proc

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

def start_all():
    ifname = setup_virtual_ip()
    server_proc = start_video_server()
    client_proc = start_mm_cmd()
    client_proc.wait()
    server_proc.kill()
    teardown_virtual_ip(ifname)
    os.system("sudo killall python python3 2> /dev/null")
    
start_all()



