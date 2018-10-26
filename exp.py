import sys
import os
import subprocess
import shutil

LOG_DIR = os.path.join(os.getcwd(), "logs")
VID_SERVER_PORT = 4443
CONV_MM_TRACE = os.path.join(LOG_DIR, "converted_mm_trace.dat")
CHROME_DIR = "/tmp/chrome_user_dir"
QOE_LOG = os.path.join(LOG_DIR, "qoe.log")

def get_python_cmds(logfile, ip_addr, headless):
    # Start ABR server.
    cmds = []
    cmds.append("sleep 1")
    cmds.append("python abr/abr_server.py --qoe-log=%s --video=%s > logs/abr_server.log 2>&1 &" % \
            (QOE_LOG, os.path.join(os.getcwd(), "server/data/videos/BigBuckBunny")))
    # Start mahimahi tailing server.
    cmds.append("python server/mm_throughput_server.py --mm-log %s/mm_downlink.log --converted-trace %s > logs/throughput_server.log 2>&1 &" % \
            (LOG_DIR, CONV_MM_TRACE))
    # Start chrome:
    headless_arg = '--headless' if headless else ''
    cmds.append("google-chrome --user-data-dir=/tmp/chrome_user_dir %s --incognito http://%s:%d/videos/BigBuckBunny > logs/chrome.log 2>&1" % \
            (headless_arg, ip_addr, VID_SERVER_PORT))
    return cmds

def mm_cmd(params):
    mm_log_file = "logs/mm_downlink.log"
    # Put in 1 BDP of buffer, assuming an average of 2 Mbps.
    rtt_ms = 80
    queue = 5 * 2 * rtt_ms / 12
    mm_queue_args="packets=%d" % queue
    link_cmd = 'mm-link %s %s --downlink-log=%s --downlink-queue=droptail\
        --downlink-queue-args="%s" <<EOF\n%s\nEOF' % \
        ("bw48.mahi", params.mm_trace, mm_log_file, mm_queue_args,
                '\n'.join(get_python_cmds(mm_log_file, params.ip_addr, params.headless)))
    delay_cmd = 'mm-delay %d %s' % (rtt_ms / 2, link_cmd)
    print delay_cmd
    return delay_cmd

def start_video_server(ip_addr):
    proc = subprocess.Popen("python3 server/video_server.py --host=%s --port=%d > logs/video_server.log 2>&1" % (ip_addr, VID_SERVER_PORT),
            stdout=sys.stdout, stderr=sys.stderr, shell=True)
    return proc

def start_mm_cmd(params):
    proc = subprocess.Popen(mm_cmd(params), stdout=sys.stdout, stderr=sys.stderr, shell=True)
    return proc


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

def start_all(params):
    if os.path.isdir(LOG_DIR):
        shutil.rmtree(LOG_DIR)
    os.makedirs(LOG_DIR)
    convert_mm_trace(params.mm_trace, CONV_MM_TRACE, 200)
    server_proc = start_video_server(params.ip_addr)
    client_proc = start_mm_cmd(params)
    client_proc.wait()
    server_proc.kill()
    parse_abr_log()
    os.system("sudo killall python python3 2> /dev/null")


