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

from readinglistlib import ReadingListReader
from icloudtabslib import iCloudTabsReader

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
			
		content_length = int(self.headers['content-length'])
		data = json.loads(self.rfile.read(content_length))
		
		action = data.get('action', '')
		type = data.get('type', '')
		
		if action == 'get':
			
			response = {'tabs': []}
			
			if type == 'rl':
				# return reading list tabs in response
				rltabs = ReadingListReader()
				for rltab in rltabs.read():
					response['tabs'].append({'title': rltab['title'], 'url': rltab['url']})
								
			elif type == 'ict':
				# return icloud tabs in response
				ictabs = iCloudTabsReader()
				for ictab in ictabs.tabs:
					response['tabs'].append({'title': ictab['title'], 'url': ictab['url']})
				
			elif type == 'all':
				# return reading list and icloud tabs in response
				# 
				rltabs = ReadingListReader()
				for rltab in rltabs.read():
					response['tabs'].append({'title': rltab['title'], 'url': rltab['url']})
				ictabs = iCloudTabsReader()
				for ictab in ictabs.tabs:
					response['tabs'].append({'title': ictab['title'], 'url': ictab['url']})

			else:
				self.send_error(400, 'Missing or invalid type for get action')
				return
			
			# manually construct response
			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			json.dump(response, self.wfile)
			# self.wfile.write(json.dumps(response))
			
		elif action == 'put':
			if type == 'rl':
				for tab in data.get('tabs', {}):
					addUrlToReadingList(tab['url'])
			elif type == 'ict':
				for tab in data.get('tabs', {}):
					addUrlToiCloudTabs(tab['url'])
			else:
				self.send_error(400, 'Missing or invalid type for put action')
				return
			
			self.send_response(200)
			
		else:
			self.send_error(400, 'Missing or invalid action')
			return
		
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

