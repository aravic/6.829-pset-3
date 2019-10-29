import sys
sys.path.append('./')
from network import trace_with_target
import argparse

parser = argparse.ArgumentParser("Trace Scaler")
parser.add_argument("--trace-in",
                    type=str,
                    required=True,
                    help="Trace to scale")
parser.add_argument("--trace-out",
                    type=str,
                    required=True,
                    help="File to write the scaled trace to")
parser.add_argument("--target-mbps",
                    type=float,
                    required=True,
                    help="Target average throughput, in Mbps")

args = parser.parse_args()

trace_with_target(args.trace_in, args.trace_out, args.target_mbps)
