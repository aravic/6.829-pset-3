import argparse
import glob
from multiprocessing.pool import ThreadPool
import numpy as np
import os
import random
import shutil
import subprocess
import tarfile
import threading
import sys
sys.path.append('./')
from network import network

def parse_args():
  argv = sys.argv[1:]
  if '--' in argv:
    remaining_args = argv[argv.index('--') + 1:]
    argv = argv[:argv.index('--')]
  else:
    remaining_args = []
  args = parser.parse_args(argv)
  return args, remaining_args

parser = argparse.ArgumentParser()
parser.add_argument('--results_dir', help='Directory to store results in/upload results from', default='eval_results/', type=str)
parser.add_argument('--team', help='Registered team name', default='', type=str)
parser.add_argument('--addr', help='Address of the leaderboard server', default='http://6829fa18.csail.mit.edu', type=str)
parser.add_argument('--upload', default=False, action='store_true')
parser.add_argument('--run', default=False, action='store_true')
args, remaining_args = parse_args()

def run_in_threadpool(f, args):
    pool = ThreadPool()
    lens = pool.map(f, args)
    pool.close()
    pool.join()
    return lens

def subprocess_cmd(command, lock=threading.Lock()):
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
    return 'python sim/run_exp.py -- --mm-trace=%s --results-dir=%s --mm-start-idx=%d -- %s' % (
        trace, results_dir, start_index,
        ' '.join(remaining_args))

def run():
    import urllib

    np.random.seed(1)

    if not os.path.isdir('/tmp/6829-smp'):
        r = urllib.urlopen('http://6829fa18.csail.mit.edu:8080/smp.tar.gz')
        with open('/tmp/6829-smp.tar.gz', 'wb') as f:
            f.write(r.read())
        tar = tarfile.open('/tmp/6829-smp.tar.gz', 'r:*')
        tar.extractall('/tmp/6829-smp')
        tar.close()
    assert(os.path.isdir('/tmp/6829-smp'))

    trace_dir = '/tmp/6829-smp/heldout/test'
    n_runs = 64

    traces = []
    cmds = []
    for fname in os.listdir(trace_dir):
      print(fname)
      if fname.endswith('.log'):
        traces.append(os.path.join(trace_dir, fname))
    np.random.shuffle(traces)

    while len(traces) < n_runs:
      traces.append(np.random.choice(traces))
    traces = traces[:n_runs]

    # rescale the throughputs.
    sample_throughputs = np.random.uniform(.3, 4, n_runs)
    rescaled_traces = []
    os.system('mkdir -p /tmp/rescaled_traces/test/')
    for trace, thr in zip(traces, sample_throughputs):
      rescaled_trace = '/tmp/rescaled_traces/%s/thr_%.2f_%s' % (
          'test', thr, os.path.basename(trace))
      network.trace_with_target(trace, rescaled_trace, thr)
      rescaled_traces.append(rescaled_trace)

    traces = rescaled_traces

    lens = run_in_threadpool(get_length, traces)
    # sample pointer from the first three-quarters of the trace.
    start_indices = [int(l * np.random.random() * .75) for l in lens]

    for trace, start_index in zip(traces, start_indices):
      cmd = cmd_gen(
          trace, start_index,
          os.path.join(args.results_dir, 'leaderboard', 'test',
                       os.path.basename(trace).split('.log')[0]))
      cmds.append(cmd)

    run_in_threadpool(subprocess_cmd, cmds)


def upload():
    import requests

    # Check if the results directory is there
    if not os.path.exists(args.results_dir):
        print("Results directory '%s' doesn't exist. Run the experiment to create directory" % args.results_dir)
        return

    if args.team == '':
        print("Please specify team name using '--team'")
        return

    # If the tarball already exists, delete
    tfname = os.path.join(args.results_dir, 'results.tar.gz')
    if os.path.exists(tfname):
        os.remove(tfname)

    # Put folder into a tarball
    print("Writing tarfile...")
    tar = tarfile.open(tfname, 'w:gz')
    tar.add(os.path.join(args.results_dir, 'leaderboard', 'test'))
    tar.close()

    with open(tfname, 'rb') as f:
        files = {"results": f}
        data = {"team": args.team}
        addr = args.addr + '/upload_file'
        r = requests.post(addr, data=data, files=files)
        print(r.content.decode())

    # Example using curl
    # curl localhost:8888/upload_file -Fteam=myteam2 -Fresults='@eval_results/results.tar.gz'

if args.run:
    run()
if args.upload:
    upload()
