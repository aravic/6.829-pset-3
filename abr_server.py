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
        default=1.0,
        help="Penalty to QoE for each second spent in startup")
parser.add_argument("--rebuffer-penalty",
        type=float,
        default=25.0,
        help="Penalty to QoE for each second spent rebuffering")
parser.add_argument("--smooth-penalty",
        type=float,
        default=10.0,
        help="Penalty to QoE for smoothness changes in bitrate")
parser.add_argument("--max-chunks",
        type=int,
        default=-1,
        help="Maximum number of chunks to watch before killing this server." \
            + " If negative, there is no limit")
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
            rebuffer_time = float(post_data['RebufferTime'] - client_dict['last_total_rebuf'])
            fetch_time_ms = post_data['lastChunkFinishTime'] - post_data['lastChunkStartTime']
            prev_br = vid.get_bitrates()[post_data['lastquality']]
            prev_chunk_rate = 0 if fetch_time_ms <= 0 else post_data['lastChunkSize'] * MILLI / fetch_time_ms
            chunk_ix = post_data['lastRequest'] + 1
            abr_input = {
                "chunk_index": chunk_ix,
                "rebuffer_sec": rebuffer_time / MILLI,
                "download_rate": prev_chunk_rate,
                "buffer_sec": post_data['buffer'],
            }
            total_qoe = 0
            next_quality = client_dict["abr"].next_quality(abr_input)
            send_data = {
                    "total_qoe": total_qoe,
                    "refresh": False,
                    "quality": next_quality,
            }

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
    pqs = [float(q) / max_pq for q in pqs]
    
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
    
    params = {
        "client_dict": {
            "video": video.Video(video_file),
            "abr": abr_alg,
            "objective": obj,
            "last_total_rebuf": 0,
            }
        }
    handler_class = make_request_handler(params)
   
    server_address = ('127.0.0.1', port)
    httpd = server_class(server_address, handler_class)
    #httpd.socket = ssl.wrap_socket(httpd.socket,
    #    keyfile="server/newplainkey.pem",
    #    certfile='server/newcert.pem', server_side=True)
    print('Listening on port ' + str(port))
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


