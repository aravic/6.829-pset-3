# This is the only file you should need to modify to do this assignment.
# 
# The AbrAlg class exposes an API for you to dictate how the next chunk of a
# video should be fetched.

class AbrAlg:
    # vid is of type video.Video
    # obj is of type objective.Objective
    def __init__(self, vid, obj):
        pass

    # Feedback is a dictionary with the following fields;
    # - 'chunk_index': the index of the chunk to be fetched next, starting at 0.
    # - 'rebuffer_sec': the number of seconds spent rebuffering immediately
    # before the previously watched chunk.
    # - 'download_rate_kbps': The average download rate (in kbps) of the previous chunk
    # - 'buffer_sec': the size of the client's playback buffer (in seconds)
    #
    # You should return an index into vid.get_bitrates(), which specifies the
    # bitrate you want to fetch for the next chunk. For example, a return value
    # of 0 indicates that the lowest quality chunk should be fetched next, while
    # len(vid.get_bitrates()) - 1 indicates the highest quality.
    def next_quality(self, feedback):
        # TODO: Fill me in!
        # Return the lowest bitrate chunk.
        return 0

