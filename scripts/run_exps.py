import numpy as np
from multiprocessing.pool import ThreadPool
import random
import argparse
import os
import subprocess
import sys
sys.path.append('./')
from network import network

parser = argparse.ArgumentParser("Main Experiment")
parser.add_argument('--trace_set', type=str, help='choose from hsdpa or fcc')
parser.add_argument("--n_train_runs", type=int, default=16)
parser.add_argument("--n_valid_runs", type=int, default=4)
parser.add_argument("--n_test_runs", type=int, default=4)
parser.add_argument('--seed', type=int, default=42)
parser.add_argument('-n', '--name', type=str, required=True)
parser.add_argument('--results_dir', type=str, default='results/')
parser.add_argument('--dry_run', action='store_true')
args = parser.parse_args()

TRACE_DIR = 'network/traces/'


def subprocess_cmd(command):
  if args.dry_run:
    print(command)
    return None
  else:
    process = subprocess.Popen(command,
                               stdout=sys.stdout,
                               stderr=sys.stderr,
                               shell=True)
    process.wait()
    return process


def get_length(trace):
  with open(trace, 'r') as f:
    return sum(1 for line in f)


def cmd_gen(trace, start_index, results_dir):
  return 'python sim/run_exp.py -- --mm-trace=%s --results-dir=%s --mm-start-idx=%d' % (
      trace, results_dir, start_index)


def run_in_threadpool(f, args):
  pool = ThreadPool()
  lens = pool.map(f, args)
  pool.close()
  pool.join()
  return lens


def main():
  np.random.seed(args.seed)
  cmds = []
  for mode, n_runs in zip(
      ['train', 'valid', 'test'],
      [args.n_train_runs, args.n_valid_runs, args.n_test_runs]):
    traces = []
    for fname in os.listdir(os.path.join(TRACE_DIR, args.trace_set, mode)):
      if fname.endswith('.log'):
        traces.append(os.path.join(TRACE_DIR, args.trace_set, mode, fname))
    np.random.shuffle(traces)
    while len(traces) < n_runs:
      traces.append(np.random.choice(traces))

    traces = traces[:n_runs]

    lens = run_in_threadpool(get_length, traces)

    # sample pointer from the first three-quarters of the trace.
    start_indices = [int(l * np.random.random() * .75) for l in lens]
    sample_throughputs = np.random.uniform(.3, 4, len(lens))
    rescaled_traces = []

    os.system('mkdir -p /tmp/rescaled_traces/%s/' % mode)
    for trace, thr, start_index in zip(traces, sample_throughputs,
                                       start_indices):
      rescaled_trace = '/tmp/rescaled_traces/%s/thr_%.2f_index_%d_%s' % (
          mode, thr, start_index, os.path.basename(trace))
      network.trace_with_target(trace, rescaled_trace, thr)
      rescaled_traces.append(rescaled_trace)
    del traces

    for trace, start_index in zip(rescaled_traces, start_indices):
      cmd = cmd_gen(
          trace, start_index,
          os.path.join(args.results_dir, args.name, mode,
                       os.path.basename(trace).split('.log')[0]))
      cmds.append(cmd)

  run_in_threadpool(subprocess_cmd, cmds)


if __name__ == '__main__':
  main()
