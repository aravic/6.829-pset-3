import numpy as np
import math
from math import ceil
import random

MTU = MTU_BYTES = 1500
BITS_IN_BYTE = 8
MEGA = 1e6
MILLI = 1e-3
KILO = 1e3


class WrapAroundException(Exception):
  pass


class Network:

  def __init__(self, mm_fname):
    l = []
    with open(mm_fname, 'r') as f:
      for line in f.read().splitlines():
        l.append(float(line))

    self.trace_fname = mm_fname
    self.l = list(l)
    self.l2 = list(l)
    self.trace_dur_sec = max(self.l2) / KILO

    for i in range(1, len(l)):
      self.l[i] = l[i] - l[i - 1]
      assert self.l[i] >= 0

    self.reset()

  def reset(self):
    self.idx = -1
    self.shift_t = 0

  # get time to download in seconds
  # input: # bytes to download
  def old_ttd(self, n_bytes):
    time_ms = 0
    bytes_accum = 0
    if self.idx is -1:
      self.idx = 0

    while bytes_accum < n_bytes:
      bytes_accum += MTU
      time_ms += self.l[self.idx]

      self.idx = (self.idx + 1) % len(self.l)

    return time_ms * MILLI

  def ttd(self, n_bytes):

    N = len(self.l)
    n_packets = int(math.ceil(n_bytes / MTU))

    assert n_packets > 1

    idx_jump = self.idx + n_packets

    time_ms = self.l2[idx_jump % N] + self.l2[-1] * int(idx_jump // N)

    if self.idx >= 0:
      time_ms -= self.l2[self.idx % N] + self.l2[-1] * int(self.idx / N)

    time_ms -= (self.shift_t * MILLI)

    self.idx = idx_jump
    self.shift_t = 0

    return time_ms * MILLI

  # lookahead_time in sec
  # return Mbps
  def get_thr_est(self, lookahead_time, no_wrap=True):
    l = self.l
    N = len(l)
    m = 0.0
    if self.idx == -1:
      i = 0
    else:
      i = self.idx % N
    c = 0

    while m / KILO < lookahead_time:
      m += l[i]
      c += 1
      i += 1
      if no_wrap and i >= N:
        raise WrapAroundException()
      i %= N

    m /= KILO
    # From total number of packets sent in m seconds, get the average
    # throughput in Mbps.
    return c * MTU_BYTES * BITS_IN_BYTE / m / MEGA

  # calls to this function advances the mahimahi pointer
  # # of bytes that can be downloaded in time seconds
  # returns in bytes, sec
  def bytes_downloadable(self, time, no_wrap=False):
    l = self.l
    N = len(l)
    m = 0.0
    if self.idx == -1:
      i = 0
    else:
      i = self.idx % N
    c = 0

    while (m + l[i]) <= time * KILO:
      m += l[i]
      c += 1
      i += 1

      if no_wrap and i >= N:
        raise WrapAroundException()

      i %= N

    if m == 0:
      assert c == 0

    self.idx = i
    return c * MTU_BYTES, m / KILO

  # total trace duration in seconds
  def get_trace_dur(self):
    return self.trace_dur_sec

  def get_mm_list(self):
    return self.l2

  def get_interval_list(self):
    return self.l

  def get_mm_ptr(self):
    return self.idx

  def get_avg_throughput_Mbps(self):
    return avg_throughput_Mbps(self.trace_fname)

  def seek_random(self):
    self.idx = random.randint(0, len(self.l) - 1)


def avg_throughput_obeo_Mbps_time(trace_file, time=None):
  ts, bs = [], []
  for line in open(trace_file).read().splitlines():
    t, b = line.split()
    ts.append(float(t) * MILLI)
    bs.append(float(b) * MILLI)

  N = len(ts)
  s = 0.
  w = 0.
  for i in range(N - 1):
    s += ((ts[i + 1] - ts[i]) * (bs[i + 1] + bs[i]) / 2.)
    w += (ts[i + 1] - ts[i])

  # throughput in Mbps.
  return s / w


# time in seconds
def avg_throughput_Mbps_time(trace_file, time):
  l = []
  for line in open(trace_file).read().splitlines():
    l.append(float(line))

  N = len(l)
  m = 0.0
  c = 0

  while m < time:
    m = (l[c % N] + (l[-1] * math.floor(c / N))) / KILO
    c += 1
  # From total number of packets sent in m milliseconds, get the average
  # throughput in Mbps.
  return c * MTU_BYTES * BITS_IN_BYTE / m / MEGA


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
      while num_packets >= 1.0 / scale:
        w.write(line)
        num_packets -= 1.0 / scale


# Scales a Mahimahi trace to achieve an average throughput of target_rate.
# target_rate is in Mbps
def trace_with_target(trace_in, trace_out, target_rate_Mbps):
  avg = avg_throughput_Mbps(trace_in)
  scale = target_rate_Mbps / avg
  print('Avg throughput %f, scaling by %f' % (avg, scale))
  scale_trace(trace_in, trace_out, scale=scale)


def plt_mahimahi_bw(log_file, N=5000):
  time_all = []
  packet_sent_all = []
  last_time_stamp = 0
  packet_sent = 0

  with open(log_file, 'r') as f:
    for line in f:
      time_stamp = int(line.split()[0])
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
  # y = np.convolve(throuput_all, np.ones(N,)/N, mode='same')
  y = throuput_all

  def running_mean(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[N:] - cumsum[:-N]) / float(N)

  x_mean = running_mean(x, N)[::N]
  y_mean = running_mean(y, N)[::N]
  return x, y, x_mean, y_mean
