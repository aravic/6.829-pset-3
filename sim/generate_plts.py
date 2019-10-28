import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.use('Agg')


def qoe_plot(result_dir, qoes):
  pqs = [qoe[0] for qoe in qoes]
  rps = [qoe[1] for qoe in qoes]
  sps = [qoe[2] for qoe in qoes]
  net_qoes = [qoe[3] for qoe in qoes]

  f, axarr = plt.subplots(2, 2, sharex=True, sharey=True)
  ax1 = axarr[0][0]
  ax1.plot(pqs)
  ax1.set_xlabel('Chunk number')
  ax1.set_ylabel('Perceptual quality score')
  root_ax = ax1

  ax2 = axarr[0][1]
  ax2.plot(pqs)
  ax2.set_xlabel('Chunk number')
  ax2.set_ylabel('Rebuffering penalty')

  ax3 = axarr[1][0]
  ax3.plot(pqs)
  ax3.set_xlabel('Chunk number')
  ax3.set_ylabel('Smoothness penalty')

  ax4 = axarr[1][0]
  ax4.plot(net_qoes)
  ax4.set_xlabel('Chunk number')
  ax4.set_ylabel('Net QOE')

  plt.tight_layout()

  plt.savefig(os.path.join(result_dir, 'qoe_plot.png'))


def buffer_plot(result_dir, buffer_lengths, ttds, delta=0.1):
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
    cur_t += ttd

  fig = plt.figure()
  plt.plot(ts, ys)
  plt.xlabel('time (sec)')
  plt.ylabel('Buffer Length (sec)')

  plt.tight_layout()
  plt.savefig(os.path.join(result_dir, 'buffer_length.png'))


def generate_plts(result_dir, qoes, buffer_lengths, ttds):
  qoe_plot(result_dir, qoes)
  buffer_plot(result_dir, buffer_plot, ttds)
