#!/usr/bin/env python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import sys
import os
import json
import ssl
import video
import argparse
import copy
import objective
import abr

MILLI = 1000.0
VIDEO_DIR = "server/data/videos"

parser = argparse.ArgumentParser("ABR Lab")
parser.add_argument("--video",
        type=str,
        required=True,
        help="video to play (must match directory under server/videos")
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
        default=-1,
        help="Maximum number of chunks to watch before killing this server." \
            + " If negative, there is no limit")
parser.add_argument("--qoe-log",
        type=str,
        default="",
        help="Where to log the ABR QoE scores")
args = parser.parse_args()

def make_request_handler(params):

    class Request_Handler(BaseHTTPRequestHandler):
        # Allow persistent connections.
        protocol_version = 'HTTP/1.1'
        
        def __init__(self, *args, **kwargs):
            BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            if 'pastThroughput' in post_data:
                # This is at the end of the video.
                return
            print(post_data)            
            if args.max_chunks >= 0 and post_data['lastRequest'] >= args.max_chunks:
                sys.exit(0)
            client_dict = params["client_dict"]
            vid = client_dict["video"]
            rebuffer_time = float(post_data['RebufferTime']) - client_dict['last_total_rebuf']
            client_dict['last_total_rebuf'] = float(post_data['RebufferTime'])
            fetch_time_ms = post_data['lastChunkFinishTime'] - post_data['lastChunkStartTime']
            prev_br = vid.get_bitrates()[post_data['lastquality']]
            prev_chunk_rate = 0 if fetch_time_ms <= 0 else post_data['lastChunkSize'] * MILLI / fetch_time_ms
            chunk_ix = post_data['lastRequest'] + 1
            rebuf_sec = rebuffer_time / MILLI
            abr_input = {
                "chunk_index": chunk_ix,
                "rebuffer_sec": rebuf_sec,
                "download_rate": prev_chunk_rate,
                "buffer_sec": post_data['buffer'],
            }
            total_qoe = 0
            next_quality = client_dict["abr"].next_quality(abr_input)
            sys.stdout.flush()
            if next_quality < 0 or next_quality >= len(vid.get_bitrates()):
                raise Exception("ABR algorithm returned quality %d, which " + \
                        "is not in the range [0, %d]" % (next_quality,
                            len(vid.get_bitrates) - 1))
            send_data = {
                    "total_qoe": total_qoe,
                    "refresh": False,
                    "quality": next_quality,
            }
            qoe = client_dict["objective"].qoe(vid.get_bitrates()[next_quality],
                                            prev_br,
                                            rebuf_sec)
            if chunk_ix == 0:
                # For first chunk, just count startup delay
                qoe = client_dict["objective"].qoe_first_chunk(
                        vid.get_bitrates()[next_quality], rebuf_sec)

            client_dict["qoe_log"].write('%d\t%f\t%f\n' % \
                    (chunk_ix, rebuf_sec, qoe))
            client_dict["qoe_log"].flush()

            end_of_video = False
            if ( chunk_ix == vid.num_chunks() ):
                send_data["refresh"] = True

            send_data_str = json.dumps(send_data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(send_data_str))
            self.send_header('Access-Control-Allow-Origin', "*")
            self.send_header('Cache-Control', 'max-age=0')
            self.end_headers()
            self.wfile.write(send_data_str)
            
        def do_GET(self):
            self.send_response(200)
            #self.send_header('Cache-Control', 'Cache-Control: no-cache, no-store, must-revalidate max-age=0')
            self.send_header('Cache-Control', 'max-age=3000')
            self.send_header('Content-Length', 20)
            self.end_headers()
            self.wfile.write("console.log('here');")

        def log_message(self, format, *args):
            return

    return Request_Handler

def parse_pqs(filename):
    pqs = open(filename).read_line()
    return [float(p) for p in pqs.split()]

def run(server_class=HTTPServer, port=8333):

    video_file = os.path.join(VIDEO_DIR, args.video, "trace.dat")
    vid = video.Video(video_file)
    pqs = vid.get_bitrates()
    max_pq = max(pqs)
    pqs = [100 * float(q) / max_pq for q in pqs]
    
    pq_dict = {}
    for br, pq in zip(vid.get_bitrates(), pqs):
        pq_dict[br] = pq

    obj = objective.Objective(pq_dict,
        args.startup_penalty,
        args.rebuffer_penalty,
        args.smooth_penalty)
    # Create identical copies that are passed to the client, in case they get
    # modified.
    obj_client = copy.deepcopy(obj)
    vid_client = copy.deepcopy(vid)
    abr_alg = abr.AbrAlg(vid_client, obj_client)
    
    qoelog = open(args.qoe_log, 'w') if len(args.qoe_log) > 0 else sys.stdout
    
    params = {
        "client_dict": {
            "video": video.Video(video_file),
            "abr": abr_alg,
            "objective": obj,
            "last_total_rebuf": 0,
            "qoe_log": qoelog, 
            }
        }
    handler_class = make_request_handler(params)
   
    server_address = ('127.0.0.1', port)
    httpd = server_class(server_address, handler_class)
    #httpd.socket = ssl.wrap_socket(httpd.socket,
    #    keyfile="server/newplainkey.pem",
    #    certfile='server/newcert.pem', server_side=True)
    print('Listening on port ' + str(port))
    sys.stdout.flush()
    httpd.serve_forever()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("Keyboard interrupted.")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

