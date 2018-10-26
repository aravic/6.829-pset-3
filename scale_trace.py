import network
import argparse

parser = argparse.ArgumentParser("Trace Scaler")
parser.add_argument("--in",
        type=str,
        required=True,
        help="Trace to scale")
parser.add_argument("--out",
        type=str,
        required=True,
        help="File to write the scaled trace to")
parser.add_argument("--target-mbps",
        type=float,
        required=True,
        help="Target average throughput, in Mbps")

network.trace_with_target(args.in, args.out, args.target_mbps)
