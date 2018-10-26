from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import sys
import os
import argparse

parser = argparse.ArgumentParser("Video server")
parser.add_argument("--host",
        type=str,
        default="127.0.0.1",
        help="Server host address")
parser.add_argument("--port",
        type=int,
        required=True,
        help="Port to listen on")
args=parser.parse_args()

curdir = os.getcwd()
SimpleHTTPRequestHandler.protocol_version = 'HTTP/1.1'

os.chdir(os.path.join(curdir, 'server/data'))
httpd = HTTPServer((args.host, args.port), SimpleHTTPRequestHandler)
print('Serving on port %d' % args.port)
sys.stdout.flush()
httpd.serve_forever()

