#!/usr/bin/env python
import sys
import os
import json
import ssl
import video
import argparse
import copy
import objective
import abr
from aiohttp import web
import socketio

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

args = parser.parse_args()
sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

CLIENT_DICT = {}

def do_POST(request):
    global CLIENT_DICT
    content_length = int(request.content_length)
    post_data = str(request.content.readexactly(content_length))
    if 'pastThroughput' in post_data:
        # This is at the end of the video.
        return
    print(post_data)           
    vid = CLIENT_DICT["video"]
    rebuffer_time = float(post_data['RebufferTime'] - CLIENT_DICT['last_total_rebuf'])
    fetch_time_ms = post_data['lastChunkFinishTime'] - post_data['lastChunkStartTime']
    abr_input = {
        "chunk_index": post_data['lastRequest'],
        "bitrate_kbps": vid.get_bitrates()[post_data['lastquality']],
        "rebuffer_sec": rebuffer_time / MILLI,
        "chunk_size_kb": post_data['lastChunkSize'],
        "download_duration_sec": fetch_time_ms / MILLI,
        "buffer_sec": post_data['buffer'],
    }
    total_qoe = 0
    next_quality = CLIENT_DICT["abr"].next_quality(abr_input)
    send_data = {
            "total_qoe": total_qoe,
            "refresh": False,
            "quality": next_quality,
    }

    end_of_video = False
    if ( post_data['lastRequest'] == vid.num_chunks() ):
        send_data["refresh"] = True
    
    send_data_str = json.dumps(send_data)
    r = web.Response(body=json.dumps(send_data_str),
            content_type='application/json',
            headers={"Content-Length": len(send_data_str),
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "max-age=0"})
    return r

def do_GET(self):
    self.send_response(200)
    #self.send_header('Cache-Control', 'Cache-Control: no-cache, no-store, must-revalidate max-age=0')
    self.send_header('Cache-Control', 'max-age=3000')
    self.send_header('Content-Length', 20)
    self.end_headers()
    self.wfile.write("console.log('here');")

def parse_pqs(filename):
    pqs = open(filename).read_line()
    return [float(p) for p in pqs.split()]

def run(port=8333):
    global CLIENT_DICT
    video_file = os.path.join(VIDEO_DIR, args.video, "trace.dat")
    vid = video.Video(video_file)
    qual_f = open(os.path.join(VIDEO_DIR, args.video, "pqs.dat"))
    pqs = [float(p) for p in qual_f.readline().split()]
    assert len(pqs) == len(vid.get_bitrates())
    
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
    
    CLIENT_DICT = {
            "video": video.Video(video_file),
            "abr": abr_alg,
            "objective": obj,
            "last_total_rebuf": 0,
            }

    app.router.add_post("/", do_POST)
    web.run_app(app, port=port)

    #httpd = server_class(server_address, handler_class)
    #httpd.socket = ssl.wrap_socket(httpd.socket,
    #    keyfile="server/newplainkey.pem",
    #    certfile='server/newcert.pem', server_side=True)
    #httpd.serve_forever()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("Keyboard interrupted.")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


