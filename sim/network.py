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

  def __init__(self, mm_fname, mm_start_idx=-1):
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

    self.idx = mm_start_idx
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
    # returns in seconds
    N = len(self.l)
    n_packets = int(math.ceil(n_bytes / MTU))

    assert n_packets > 1

    idx_jump = self.idx + n_packets

    time_ms = self.l2[idx_jump % N] + self.l2[-1] * int(idx_jump / N)

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
