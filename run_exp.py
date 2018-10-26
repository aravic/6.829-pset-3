import argparse
import exp

parser = argparse.ArgumentParser("Main Experiment")
parser.add_argument("--mm-trace",
        type=str,
        default="bw3.mahi",
        help="Mahimahi link trace to use")

args = parser.parse_args()
ifname = setup_virtual_ip()
exp.start_all(args.mm_trace)
teardown_virtual_ip(ifname)

