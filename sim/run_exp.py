import argparse
import copy
import json
import logging
import os
import sys

import numpy as np
sys.path.append('./')
from your_code import abr, objective, video
from absl import app
from sim import network
from sim.env import Env
from sim.generate_plts import generate_plts
import utils

KILO = 1000.0
BITS_IN_BYTE = 8
CHUNK_DUR = 4.0

parser = argparse.ArgumentParser("Run experiment using Simulator")
parser.add_argument("--video",
                    type=str,
                    default='real/data/videos/BigBuckBunny/trace.dat',
                    help="Root directory of video to play")
parser.add_argument("--startup-penalty",
                    type=float,
                    default=5.0,
                    help="Penalty to QoE for each second spent in startup")
parser.add_argument("--rebuffer-penalty",
                    type=float,
                    default=25.0,
                    help="Penalty to QoE for each second spent rebuffering")
parser.add_argument("--smooth-penalty",
                    type=float,
                    default=1.0,
                    help="Penalty to QoE for smoothness changes in bitrate")
parser.add_argument("--max-chunks",
        type=int,
        default=50,
        help="Maximum number of chunks to watch before killing this server." \
            + " If negative, there is no limit")
parser.add_argument("--mm-trace",
                    type=str,
                    required=True,
                    help="Mahimahi link trace to use")
parser.add_argument('--mm-start-idx', type=int, default=0)
parser.add_argument('--results-dir', type=str, required=True)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

parser.add_argument('--rb', action='store_true')
# INSTRUCTOR ONLY ARGS
parser.add_argument('--instructor-mpc', action='store_true')
parser.add_argument('--instructor-bb', action='store_true')


def parse_args(argv):
  if '--' in argv:
    remaining_args = argv[argv.index('--') + 1:]
    argv = argv[:argv.index('--')]
  else:
    remaining_args = []
  args = parser.parse_args(argv)
  return args, remaining_args


def main(argv):

  args, remaining_args = parse_args(argv[1:])
  vid = video.Video(args.video)

  if args.max_chunks is not None:
    vid.set_max_chunks(args.max_chunks)

  pqs = vid.get_bitrates()
  max_pq = max(pqs)
  pqs = [100 * float(q) / max_pq for q in pqs]

  pq_dict = {}
  for br, pq in zip(vid.get_bitrates(), pqs):
    pq_dict[br] = pq

  obj = objective.Objective(pq_dict, args.startup_penalty,
                            args.rebuffer_penalty, args.smooth_penalty)
  net = network.Network(args.mm_trace, args.mm_start_idx)
  env = Env(vid, obj, net)
  obj_client = copy.deepcopy(obj)
  vid_client = copy.deepcopy(vid)

  if args.instructor_mpc:
    from mpc.mpc import AbrAlg
    abr_alg_fn = AbrAlg
  elif args.instructor_bb:
    from bb.bb import AbrAlg
    abr_alg_fn = AbrAlg
  elif args.rb:
    from your_code.rb import AbrAlg
    abr_alg_fn = AbrAlg
  else:
    abr_alg_fn = abr.AbrAlg

  abr_alg = abr_alg_fn(vid_client, obj_client, remaining_args)

  total_rebuf_sec = 0
  rebuf_sec = None
  prev_chunk_rate = None
  buff = env.get_buffer_size()
  buff_lens = [buff]
  ttds = []

  for i in range(vid.num_max_chunks()):
    feedback = {
        "chunk_index": i,
        "rebuffer_sec": rebuf_sec,
        "download_rate_kbps": prev_chunk_rate,
        "buffer_sec": buff,
    }

    quality = abr_alg.next_quality(**feedback)

    ttd, rebuf_sec, smooth_pen, prev_chunk_rate = env.step(quality)

    buff = env.get_buffer_size()

    if i > 0:
      total_rebuf_sec += rebuf_sec

    buff_lens.append(buff)
    ttds.append(ttd)

  tot_qoe = env.get_total_qoe()
  avg_qoe = tot_qoe / vid.num_max_chunks()

  print('Avg QoE: ', avg_qoe)
  print('Total Rebuf (sec): ', total_rebuf_sec)
  print('Avg Down Rate (Mbps): %.2f' % (env.get_avg_down_rate_kbps() / KILO))

  i = 0
  for l in zip(*env.get_avg_qoe_breakdown(4)):
    print('%d/%d part Qoe-Qual: %.2f, rp: %.2f, sp: %.2f, total-qoe: %.2f' %
          (i, 4, l[0], l[1], l[2], l[3]))
    i += 1

  for l in zip(*env.get_avg_qoe_breakdown(1)):
    print('%d/%d part Qoe-Qual: %.2f, rp: %.2f, sp: %.2f, total-qoe: %.2f' %
          (0, 1, l[0], l[1], l[2], l[3]))

  # print('Avg network throughput (Mbps): %.2f'% network.avg_throughput_Mbps_time(args.mm_trace, vid.num_max_chunks()* 4.0))
  if args.results_dir is not None:
    utils.mkdir_if_not_exists(args.results_dir)
    env.log_qoe(os.path.join(args.results_dir, 'qoe.txt'))

  with open(os.path.join(args.results_dir, 'results.json'), 'w') as f:
    (qual, ), (rp, ), (sp, ), (qoe, ) = env.get_avg_qoe_breakdown(1)
    json.dump(dict(avg_quality_score=qual,
                   avg_rebuf_penalty=rp,
                   avg_smoothness_penalty=sp,
                   avg_net_qoe=qoe),
              f,
              indent=4,
              sort_keys=True)
  generate_plts(args.results_dir, env.get_bitrates(), env.get_qoes(),
                buff_lens, ttds, args.mm_trace, args.mm_start_idx)


if __name__ == '__main__':
  # main()
  app.run(main)
