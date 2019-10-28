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

exp.start_all(args.mm_trace, args.ip_addr)
