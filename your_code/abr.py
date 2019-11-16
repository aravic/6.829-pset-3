# This is the only file you should need to modify to do this assignment.
#
# The AbrAlg class exposes an API for you to dictate how the next chunk of a
# video should be fetched.
import argparse
parser = argparse.ArgumentParser()
# TODO: Add the required command line arguments to your abr algorithm here (if needed).
# See below for an example. You can specify values for the arguments added here by passing
# them after a *second* '--' delimiter. Example invokation:
# python sim/run_exp.py -- --mm-trace=network/traces/cellular/Verizon1.dat -- --param1=2
parser.add_argument('--param1', type=float, default=1)



class AbrAlg:
  # vid is of type video.Video
  # obj is of type objective.Objective
  def __init__(self, vid, obj, cmdline_args):
    # Use parameters from self.args to define your abr algorithm.
    self.vid = vid
    self.obj = obj
    self.args = parser.parse_args(cmdline_args)

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

    quality = 0
    # TODO: Change the quality to the quality of the bitrate that you want
    # to fetch next.

    assert quality >= 0 and quality < len(self.vid.get_bitrates())
    return quality
