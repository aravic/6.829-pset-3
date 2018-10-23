from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import os

curdir = os.getcwd()
keyfile = os.path.join(curdir, 'server/newplainkey.pem')
certfile = os.path.join(curdir, 'server/newcert.pem')

os.chdir(os.path.join(curdir, 'server/data'))
httpd = HTTPServer(('127.0.0.1', 4443), SimpleHTTPRequestHandler)
#httpd.socket = ssl.wrap_socket (httpd.socket, keyfile=keyfile,
#        certfile=certfile,
#        server_side=True)
httpd.serve_forever()

