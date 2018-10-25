import sys
import os
import argparse
import subprocess
import shutil

parser = argparse.ArgumentParser("Main Experiment")
parser.add_argument("--mm-trace",
        type=str,
        default="bw3.mahi",
        help="Mahimahi link trace to use")
parser.add_argument("--video",
        type=str,
        default="BigBuckBunny",
        help="Video to watch")

args = parser.parse_args()

IP_ADDR = "10.0.0.1"
VID_SERVER_PORT = 4443
CONV_MM_TRACE = "logs/converted_mm_trace.dat"
CHROME_DIR = "/tmp/chrome_user_dir"
QOE_LOG = "logs/qoe.log"

def get_python_cmds(logfile):
    # Start ABR server.
    cmds = []
    cmds.append("python abr_server.py --qoe-log=%s --video=%s > logs/abr_server.log 2>&1 &" % (QOE_LOG, args.video))
    # Start mahimahi tailing server. TODO
    cmds.append("python mm_throughput_server.py --mm-log logs/mm_downlink.log --converted-trace %s > logs/throughput_server.log 2>&1 &" % CONV_MM_TRACE)
    # Start chrome:
    #cmds.append("google-chrome --user-data-dir=/tmo/chrome_user_dir --incognito")
    cmds.append("google-chrome --user-data-dir=/tmp/chrome_user_dir --incognito http://%s:%d/videos/%s > logs/chrome.log 2>&1" % (IP_ADDR, VID_SERVER_PORT, args.video))
    return cmds

def mm_cmd():
    mm_log_file = "logs/mm_downlink.log"
    # Put in 1 BDP of buffer, assuming an average of 2 Mbps.
    rtt_ms = 80
    queue = 5 * 2 * rtt_ms / 12
    print args.mm_trace
    mm_queue_args="packets=%d" % queue
    link_cmd = 'mm-link %s %s --downlink-log=%s --downlink-queue=droptail\
        --downlink-queue-args="%s" <<EOF\n%s\nEOF' % \
        ("bw48.mahi", args.mm_trace, mm_log_file, mm_queue_args,
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

# 'tracefile': the mahimahi trace file
# 'bucket': Number of milliseconds per bucket.
# Converts mahimahi format to fixed timesteps, where each timestep
# records the average bandwidth over the last 'bucket' milliseconds.
def convert_mm_trace(tracefile, outfile, bucket):
    with open(outfile, 'w') as out:
        t = 0
        t_offset = 0
        # bits
        pkt_size = (1504 * 8)
        pkts = 0
        # Write this many entries
        left_to_write = 60 * 10 * 1000 / bucket
        while left_to_write > 0:
            f = open(tracefile)
            offset = 0
            for line in f:
                ts = int(line)
                offset = ts
                ts += t_offset
                if ts > t + bucket:
                    # Timestamp is midpoint of bandwidth in that bucket.
                    out.write("%d %d\n" % (t, (pkts * pkt_size) / bucket))
                    left_to_write -= 1
                    if left_to_write == 0:
                        break
                    t += bucket
                    pkts = 0
                pkts += 1
            f.close()
            t_offset += offset

def parse_abr_log():
    avg_qoe = 0
    nchunks = 0
    rebuf = 0
    for line in open(QOE_LOG):
        parts = line.split()
        avg_qoe += float(parts[-1])
        rebuf += float(parts[1])
        nchunks += 1
    if nchunks == 0:
        print 'No chunks fetched'
        return 0
    avg_qoe /= nchunks
    print '%d chunks fetched, total rebuffer time = %fs, Avg QoE = %f' % (nchunks, rebuf, avg_qoe)
    return avg_qoe

def start_all():
    if not os.path.isdir("logs/"):
        os.makedirs("logs/")
    convert_mm_trace(args.mm_trace, CONV_MM_TRACE, 500)
    ifname = setup_virtual_ip()
    server_proc = start_video_server()
    client_proc = start_mm_cmd()
    client_proc.wait()
    server_proc.kill()
    teardown_virtual_ip(ifname)
    parse_abr_log()
    os.system("sudo killall python python3 2> /dev/null")

start_all()



