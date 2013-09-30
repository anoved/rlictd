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

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import base64
import ssl
import subprocess
import json

# Allow connections only from the specific IP addresses given in this list.
# Allow connections from any IP address if this list is empty.
IP_WHITELIST = []

# Credentials for basic HTTP authentication
AUTH_USERNAME = "foo"
AUTH_PASSWORD = "bar"

# Server address configuration
SERVER_NAME = "192.168.1.5"
SERVER_PORT = 8081

class rlictdRequestHandler(BaseHTTPRequestHandler):

	#
	# Return value:
	#	True if client is authorized
	#	False if client is not authorized
	#
	# Side effects:
	#	Sends error response to client if and only if client is not authorized.
	#
	def authorized(self):

		# restrict access to clients in the IP whitelist
		if len(IP_WHITELIST) > 0 and self.client_address[0] not in IP_WHITELIST:
			self.send_error(403, "Disallowed IP address")
			return False
		
		# require authorization
		if 'Authorization' not in self.headers:
			self.send_error(401, "Authorization required")
			return False
		
		# get authorization values
		authtoken = self.headers['Authorization'].split(' ', 1)[1]
		username, password = base64.b64decode(authtoken).split(':', 1)
		
		# require correct authentication
		if (username != AUTH_USERNAME) or (password != AUTH_PASSWORD):
			self.send_error(401, "Authorization failed")
			return False
		
		return True
	
	def do_GET(self):
		
		if not self.authorized():
			return
		
		self.send_response(200)

	def do_POST(self):
		
		if not self.authorized():
			return

		# should respond OK immediately or after processing?
		self.send_response(200)
			
		content_length = int(self.headers['content-length'])
		body = self.rfile.read(content_length)
		tabs = json.loads(body)
		
		for tab in tabs:
			addUrlToiCloudTabs(tab['URL'])
		

def addUrlToiCloudTabs(url):
	# -g means the application is not brought to the foreground
	cmd = ['/usr/bin/open', '-a', 'Safari', '-g', url]
	subprocess.call(cmd)

def addUrlToReadingList(url):
	cmd = ['/usr/bin/osascript', '-e', 'tell application "Safari" to add reading list item "%s"' % url]
	subprocess.call(cmd)
 
server = HTTPServer((SERVER_NAME, SERVER_PORT), rlictdRequestHandler)
server.socket = ssl.wrap_socket(server.socket, certfile='server.pem', server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)

try:
	server.serve_forever()
except KeyboardInterrupt:
	pass

