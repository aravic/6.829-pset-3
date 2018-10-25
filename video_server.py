from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
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
keyfile = os.path.join(curdir, 'server/newplainkey.pem')
certfile = os.path.join(curdir, 'server/newcert.pem')

class PersistentHTTPRequestHandler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __init__(self, *args, **kwargs):
        SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)


os.chdir(os.path.join(curdir, 'server/data'))
httpd = HTTPServer((args.host, args.port), PersistentHTTPRequestHandler)
#httpd.socket = ssl.wrap_socket (httpd.socket, keyfile=keyfile,
#        certfile=certfile,
#        server_side=True)
httpd.serve_forever()

