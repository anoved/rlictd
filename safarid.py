#!/usr/bin/python

# This server script responds to queries from compatible browser extensions
# (or, conceivably, other programs - possibly other instances of itself invoked
# in an interactive way?). Supported queries take two general forms:
#
# 1. Requests for a list of Reading List URLs and/or iCloud Tabs URLs
# 2. Requests to add included URLs to Reading List or iCloud Tabs
#
# iCloudTabsReader and/or ReadingListReader are used to support type 1 requests.
# Type 2 requests are handled by opening the URLs with Safari (to add them to
# iCloud Tabs, presuming the user's account is active) or using osascript to
# add them to reading list using the appropriate AppleScript action.
#
# Authentication and connection whitelisting should certainly be applied.

try:
	from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
except:
	from http.server import HTTPServer, BaseHTTPRequestHandler

import cgi

class SafariServer(BaseHTTPRequestHandler):

	def do_POST(self):
	
		content_length = int(self.headers['content-length'])
		body = self.rfile.read(content_length)
		print body
		
		self.send_response(200)
		self.send_header("Content-type", "text/plain")
		self.end_headers()
		self.wfile.write("OK".encode("utf-8"))

port = 8081
server = HTTPServer(('192.168.1.5', port), SafariServer)
try:
	server.serve_forever()
except KeyboardInterrupt:
	pass


