import numpy as np
import argparse
parser = argparse.ArgumentParser()
# TODO: Add the required command line arguments to your abr algorithm here.
# See below for an example
parser.add_argument('--past_n_throughput_vals', type=float, default=5)


class AbrAlg:
  # vid is of type video.Video
  # obj is of type objective.Objective
  def __init__(self, vid, obj, cmdline_args):
    # Use parameters from self.args to define your abr algorithm.
    self.vid = vid
    self.obj = obj
    self.args = parser.parse_args(cmdline_args)

    self._prev_download_rates = []
    self._past_n_throughput_vals = self.args.past_n_throughput_vals

  ########### Args #####################
  # - 'chunk_index': the index of the chunk to be fetched next, starting at 0.
  # - 'rebuffer_sec': the number of seconds spent rebuffering immediately
  # before the previously watched chunk.
  # - 'download_rate_kbps': The average download rate (in kbps) of the previous chunk
  # - 'buffer_sec': the size of the client's playback buffer (in seconds)
  #
  ########### INITIALIZATION #############
  # Please note that for the first chunk when there is no network feedback yet
  # some of the above arguments take the following default values
  # chunk_index = 0
  # rebuffer_sec = None
  # download_rate_kbps = None
  # buffer_sec = 0

  # Please take special care of the None values above.

  ########### Return Quality ############
  # You should return an index into vid.get_bitrates(), which specifies the
  # bitrate you want to fetch for the next chunk. For example, a return value
  # of 0 indicates that the lowest quality chunk should be fetched next, while
  # len(vid.get_bitrates()) - 1 indicates the highest quality.

  def next_quality(self, chunk_index, rebuffer_sec, download_rate_kbps,
                   buffer_sec):
    """
      Simple algorithm that looks at the mean of the past 5 throughput samples
      and picks a quality whose bitrate is lower than this estimate.
      It does *not* take the current buffer levels as its input.
    """

    if download_rate_kbps is None:
      # First chunk case -> we have no estimate.
      # Simply, use a default quality
      quality = 0
    else:
      # Consider only the latest self._past_n_throughput_vals
      if len(self._prev_download_rates) == self._past_n_throughput_vals:
        self._prev_download_rates = self._prev_download_rates[1:]

      self._prev_download_rates.append(download_rate_kbps)
      mean_rate = np.mean(self._prev_download_rates)
      bitrates = self.vid.get_bitrates()

      # Pick the maximum bitrate that is lower than the mean_rate
      for br in sorted(bitrates, reverse=True):
        if br <= mean_rate:
          break

      quality = bitrates.index(br)

    assert quality >= 0 and quality < len(self.vid.get_bitrates())
    return quality
