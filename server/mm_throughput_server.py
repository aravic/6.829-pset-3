from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import sys
import os
import json
import subprocess
import argparse
import select
import time

parser = argparse.ArgumentParser("Mahimahi Log Tailer")
parser.add_argument("--mm-log",
        type=str,
        required=True,
        help="Mahimahi log to tail")
parser.add_argument("--converted-trace",
        type=str,
        required=True,
        help="Mahimahi trace, converted")
parser.add_argument("--port",
        type=int,
        default=8001,
        help="Port to listen on")
args = parser.parse_args()

def make_request_handler(params):
    class RequestHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def __init__(self, *args, **kwargs):
            BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

        def do_GET(self):
            print 'Got request'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'max-age=0')
            self.send_header('Access-Control-Allow-Origin', "*")
            self.send_header('Content-Length', len(params["data"]))
            self.end_headers()
            self.wfile.write(params["data"])

    return RequestHandler

def run():
    # These 2 lines should go together as closely as posisble.
    # Establishes a relationship between time.time() and the Mahimahi shell timestamp
    start_ms = int(time.time() * 1000) + 1
    last_line = subprocess.check_output("tail -n 1 %s" % args.mm_log, shell=True)
    mm_ms = int(last_line.split()[0])
    # The mahimahi shell doesn't start at time 0, so 
    for line in open(args.mm_log):
        if line.startswith('#'):
            continue
        first_ms = int(line.strip().split()[0])
        mm_ms -= first_ms
        break
    print 'Start ms = %d, mm_offset = %d' % (start_ms, mm_ms)
    # This is the system time corresponding to time 0 on the trace.
    time_offset = start_ms - mm_ms
    data = []
    for line in open(args.converted_trace):
        nums = line.strip().split()
        data.append("%d %d" % (int(nums[0]) + time_offset, int(nums[1])))

    data_str = '\n'.join(data)

    params = {
        "data": data_str,
        }
    print data_str
    handler_class = make_request_handler(params)
    server_address = ("127.0.0.1", args.port)
    httpd = HTTPServer(server_address, handler_class)
    print 'Listening on port %d' % args.port
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

