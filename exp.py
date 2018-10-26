import sys
import os
import subprocess
import shutil

LOG_DIR = os.path.join(os.getcwd(), "logs")
IP_ADDR = "10.0.0.1"
VID_SERVER_PORT = 4443
CONV_MM_TRACE = os.path.join(LOG_DIR, "converted_mm_trace.dat")
CHROME_DIR = "/tmp/chrome_user_dir"
QOE_LOG = os.path.join(LOG_DIR, "qoe.log")

def get_python_cmds(logfile):
    # Start ABR server.
    cmds = []
    cmds.append("sleep 1")
    cmds.append("python abr/abr_server.py --qoe-log=%s --video=%s > logs/abr_server.log 2>&1 &" % \
            (QOE_LOG, os.path.join(os.getcwd(), "server/data/videos/BigBuckBunny")))
    # Start mahimahi tailing server. TODO
    cmds.append("python server/mm_throughput_server.py --mm-log %s/mm_downlink.log --converted-trace %s > logs/throughput_server.log 2>&1 &" % \
            (LOG_DIR, CONV_MM_TRACE))
    # Start chrome:
    #cmds.append("google-chrome --user-data-dir=/tmo/chrome_user_dir --incognito")
    cmds.append("google-chrome --user-data-dir=/tmp/chrome_user_dir --incognito http://%s:%d/videos/BigBuckBunny > logs/chrome.log 2>&1" % (IP_ADDR, VID_SERVER_PORT))
    return cmds

def mm_cmd(trace):
    mm_log_file = "logs/mm_downlink.log"
    # Put in 1 BDP of buffer, assuming an average of 2 Mbps.
    rtt_ms = 80
    queue = 5 * 2 * rtt_ms / 12
    mm_queue_args="packets=%d" % queue
    link_cmd = 'mm-link %s %s --downlink-log=%s --downlink-queue=droptail\
        --downlink-queue-args="%s" <<EOF\n%s\nEOF' % \
        ("bw48.mahi", trace, mm_log_file, mm_queue_args,
                '\n'.join(get_python_cmds(mm_log_file)))
    delay_cmd = 'mm-delay %d %s' % (rtt_ms / 2, link_cmd)
    print delay_cmd
    return delay_cmd

def start_video_server():
    proc = subprocess.Popen("python3 server/video_server.py --host=%s --port=%d > logs/video_server.log 2>&1" % (IP_ADDR, VID_SERVER_PORT),
            stdout=sys.stdout, stderr=sys.stderr, shell=True)
    return proc

def start_mm_cmd(trace):
    proc = subprocess.Popen(mm_cmd(trace), stdout=sys.stdout, stderr=sys.stderr, shell=True)
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
        # Write 15 minutes worth of data.
        left_to_write = 60 * 15 * 1000 / bucket
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
        rebuf += float(parts[2])
        nchunks += 1
    if nchunks == 0:
        print 'No chunks fetched'
        return 0
    avg_qoe /= nchunks
    print '%d chunks fetched, total rebuffer time = %fs, Avg QoE = %f' % (nchunks, rebuf, avg_qoe)
    return avg_qoe

def start_all(mm_trace):
    if os.path.isdir(LOG_DIR):
        shutil.rmtree(LOG_DIR)
    os.makedirs(LOG_DIR)
    convert_mm_trace(mm_trace, CONV_MM_TRACE, 200)
    ifname = setup_virtual_ip()
    server_proc = start_video_server()
    client_proc = start_mm_cmd(mm_trace)
    client_proc.wait()
    server_proc.kill()
    teardown_virtual_ip(ifname)
    parse_abr_log()
    os.system("sudo killall python python3 2> /dev/null")


