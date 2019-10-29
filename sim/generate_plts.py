import math
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import os

MTU = MTU_BYTES = 1500
BITS_IN_BYTE = 8
MEGA = 1e6
MILLI = 1e-3
KILO = 1e3


def qoe_plot(result_dir, qoes):
  pqs = [qoe[0] for qoe in qoes]
  rps = [qoe[1] for qoe in qoes]
  sps = [qoe[2] for qoe in qoes]
  net_qoes = [qoe[3] for qoe in qoes]

  f, axarr = plt.subplots(2, 2, sharex=True)
  ax1 = axarr[0][0]
  ax1.plot(pqs)
  ax1.set_xlabel('Chunk number')
  ax1.set_ylabel('Perceptual quality score')
  root_ax = ax1

  ax2 = axarr[0][1]
  ax2.plot(rps)
  ax2.set_xlabel('Chunk number')
  ax2.set_ylabel('Rebuffering penalty')

  ax3 = axarr[1][0]
  ax3.plot(sps)
  ax3.set_xlabel('Chunk number')
  ax3.set_ylabel('Smoothness penalty')

  ax4 = axarr[1][1]
  ax4.plot(net_qoes)
  ax4.set_xlabel('Chunk number')
  ax4.set_ylabel('Net QOE')

  plt.tight_layout()
  plt.savefig(os.path.join(result_dir, 'qoe_plot.png'))


def buffer_plot(ax, buffer_lengths, ttds, delta=0.1):
  """
    Args:
      buffer_lengths: List[float] len == T + 1
      ttds: List[float]: len == T
      delta: Inter sample spacing in seconds.
  """
  ts = []
  ys = []
  prev_buf = ttds[0]
  cur_t = 0

  for i, (ttd, buf) in enumerate(zip(ttds[1:], buffer_lengths)):
    # interpolate between prev_buf and buf
    n_interpols = int(math.ceil(ttd / delta))
    n_interpols = min(10, n_interpols)

    ts.extend(list(np.linspace(cur_t, cur_t + ttd, 2 + n_interpols)))
    ys.extend(list(np.maximum(np.linspace(prev_buf, buf, 2 + n_interpols), 0)))
    prev_buf = buf
    cur_t += ttd

  ax.plot(ts, ys)
  ax.set_xlabel('time (sec)')
  ax.set_ylabel('Buffer Length (sec)')


def plt_mahimahi_bw(ax, trace_file, start_idx, total_time, N=10):

  trace = []
  with open(trace_file, 'r') as f:
    for line in f:
      time_stamp = int(line.split()[0])
      trace.append(int(line.split()[0]))

  start_t = trace[start_idx]
  trace_np = np.int32(trace)

  while (trace[-1] - start_t) * MILLI < total_time:
    trace.extend(trace_np + trace[-1])

  trace = trace[start_idx:]
  trace = np.int32(trace) - trace[0]

  filtered_trace = []
  for t in trace:
    if t * MILLI <= total_time:
      filtered_trace.append(t)

  trace = filtered_trace

  time_all = []
  packet_sent_all = []
  last_time_stamp = 0
  packet_sent = 0

  for time_stamp in trace:
    if time_stamp == last_time_stamp:
      packet_sent += 1
      continue
    else:
      time_all.append(last_time_stamp)
      packet_sent_all.append(packet_sent)
      packet_sent = 1
      last_time_stamp = time_stamp

  time_window = np.array(time_all[1:]) - np.array(time_all[:-1])
  throuput_all = MTU * \
                 BITS_IN_BYTE * \
                 np.array(packet_sent_all[1:]) / \
                 time_window * \
                 KILO / \
                 MEGA

  x = np.array(time_all[1:]) * MILLI
  y = throuput_all

  def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[N:] - cumsum[:-N]) / float(N)

  x_mean = running_mean(x, N)[::N]
  y_mean = running_mean(y, N)[::N]

  ax.plot(x_mean,
          y_mean,
          label='Throughput (Mean: %.3f Mbps)' % np.mean(y_mean))
  ax.set_xlabel('Time (sec)')
  ax.set_ylabel('link Capacity (Mbps)')
  ax.legend()


def plt_bitrates(ax, bitrates, ttds):
  xs = []
  ys = []
  prev_time = 0
  for br, ttd in zip(bitrates, ttds):
    xs.append(prev_time)
    ys.append(br)

    xs.append(prev_time + ttd)
    ys.append(br)
    prev_time += ttd

  ax.plot(xs, ys)
  ax.set_xlabel('Time (sec)')
  ax.set_ylabel('Bitrate (Kbps)')


def plt_trio(result_dir, bitrates, buffer_lengths, ttds, trace_file,
             start_idx):
  """Plots bitrate, buffer and mahimahi throughput vertically in a single plot."""

  f, axarr = plt.subplots(3, 1)
  plt_bitrates(axarr[0], bitrates, ttds)
  buffer_plot(axarr[1], buffer_lengths, ttds)
  plt_mahimahi_bw(axarr[2], trace_file, start_idx, sum(ttds))

  plt.tight_layout()
  plt.savefig(os.path.join(result_dir, 'buffer-bitrate-throughput.png'))


def generate_plts(result_dir, bitrates, qoes, buffer_lengths, ttds, trace_file,
                  start_idx):
  qoe_plot(result_dir, qoes)
  plt_trio(result_dir, bitrates, buffer_lengths, ttds, trace_file, start_idx)
