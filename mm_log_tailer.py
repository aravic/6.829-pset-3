from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import sys
import os
import json
import subprocess
import argparse

parser = argparse.ArgumentParser("Mahimahi Log Tailer")
parser.add_argument("--mm-log",
        type=str,
        required=True,
        help="Mahimahi log to tail")

args = parser.parse_args()

def make_request_handler(params):
    class RequestHandler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def __init__(self, *args, **kwargs):
            BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

        def do_GET(self):
            # Parse all the lines from stdout.
            tot_bytes = 0
            while True:
                line = params["f"].stdout.readline():
                if line:
                    if '#' in line:
                        tot_bytes += 1504
                else:
                    break
            t = time.time()
            delta = t - params["t"]
            cap = str(int(8. * tot_bytes / delta / 1024))
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'max-age=0')
            self.send_header('Content-Length', len(cap))
            self.end_headers()
            self.wfile.write(cap)
            params["t"] = t

    return RequestHandler

