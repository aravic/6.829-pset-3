import sys

MTU_BYTES = 1500
BITS_IN_BYTE = 8

def avg_throughput_Mbps(trace_file):
    m = 0.0
    c = 0
    for line in open(trace_file).read().splitlines():
        m = max(float(line), m)
        c += 1
    # From total number of packets sent in m milliseconds, get the average
    # throughput in Mbps.
    return c * MTU_BYTES * BITS_IN_BYTE / (1000.0 * m)
    
# Scales trace by the given factor. This isn't as straightforward as multiplying
# each line by <scale>; that would achieve the correct average throughput but would
# be 'stretched out'. Instead, we keep accumulating packets until we get 1,
# at which point we send it.
def scale_trace(trace_in, trace_out, scale=1.0):
    num_packets = 0.0
    with open(trace_out, 'w') as w:
        for line in open(trace_in):
            num_packets += 1.0
            if num_packets >= 1.0/scale:
                w.write(line)
                num_packets -= 1.0/scale


# Scales a Mahimahi trace to achieve an average throughput of target_rate.
# target_rate is in Mbps
def trace_with_target(trace_in, trace_out, target_rate_Mbps):
    avg = avg_throughput_Mbps(trace_in)
    scale = target_rate_Mbps/avg
    print 'Avg throughput %f, scaling by %f' % (avg, scale)
    scale_trace(trace_in, trace_out, scale=scale)

trace_with_target(sys.argv[1], sys.argv[2], float(sys.argv[3]))
