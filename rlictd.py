#!/usr/bin/python

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
	
	#
	# Respond to an HTTP GET request. Doesn't currently do anything besides
	# confirm connection - useful for checking HTTPS and authentication setup.
	#
	def do_GET(self):
		if not self.authorized():
			return
		self.send_response(200, "OK")
	
	#
	# Respond to an HTTP POST request (presumably a request from an rlictd
	# client). Request content is read as JSON data; 'action' property must be
	# 'get' or 'put', indicating whether this is a request for URLs from rlictd
	# (get) or a delivery of URLs for rlictd (put). The 'type' property may be
	# 'rl' (Reading List) or 'ict' (iCloud Tabs) to indicate which collection
	# is the target of the action ('get' actions may specify 'all' as the type
	# to request URLs from both collections at once). 'put' actions should be
	# accompanied by a 'tabs' property containing a list of dicts, each
	# containing [at least] a 'url' property. 'get' actions are sent a JSON
	# response; the response contains a 'tabs' property containing a dict with
	# two properties, 'ict' and 'rl', each of which is a list of dicts
	# containing 'title' and 'url' properties. (Only the requested tab type list
	# is populated in the response.)
	#
	def do_POST(self):
		
		if not self.authorized():
			return
		
		# read the request and parse it as JSON
		content_length = int(self.headers['content-length'])
		data = json.loads(self.rfile.read(content_length))
		
		# get the required parameters
		action = data.get('action', '')
		type = data.get('type', '')
		
		if action == 'get':
			
			# get type must be specified as rl (Reading List), ict (iCloud Tabs), or all (both)
			if (type != 'rl') and (type != 'ict') and (type != 'all'):
				self.send_error(400, 'Missing or invalid type for get action')
				return
			
			# construct the JSON response containing tabs of requested type
			response = {'tabs': {'ict': [], 'rl': []}}
			if type == 'rl':
				response['tabs']['rl'] = getRlUrls(ReadingListReader().read())
			elif type == 'ict':
				response['tabs']['ict'] = getIctUrls(iCloudTabsReader().tabs)
			elif type == 'all':
				response['tabs']['rl'] = getRlUrls(ReadingListReader().read())
				response['tabs']['ict'] = getIctUrls(iCloudTabsReader().tabs)
			
			# send the response back to the client
			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			json.dump(response, self.wfile)
			
		elif action == 'put':
			
			# put type must be specified as rl (Reading List) or ict (iCloud Tabs)
			if (type != 'rl') and (type != 'ict'):
				self.send_error(400, 'Missing or invalid type for put action')
				return
			
			# deliver tabs received from client to the indicated collection
			for tab in data.get('tabs', {}):
				putUrl(tab['url'], type)
			
			# simply confirm completion
			self.send_response(200)
			
		else:
			self.send_error(400, 'Missing or invalid action')
			return

# relies on ReadingListReader().read() and iCloudTabsReader().tabs both
# returning lists of dicts containing title and url properties. If these reader
# module behaviors change, separate getUrls methods will be needed.
# Since the title/url property names match, we could return tabs - but this
# lets us filter out other unnecessary properties.
def getRlUrls(tabs):
	urls = []
	for tab in tabs:
		urls.append({'title': tab['title'], 'url': tab['url']})
	return urls

def getIctUrls(tabs):
	devices = list(set([tab['device'] for tab in tabs]))
	results = {}
	for device in devices:
		results[device] = [{'title': tab['title'], 'url': tab['url']} for tab in tabs if tab['device'] == device]
	return results

# deliver url to collection identified by type, which determines command
# returns command exit status: 0 on success, nonzero otherwise
def putUrl(url, type):
	if type == 'rl':
		cmd = ['/usr/bin/osascript', '-e', 'tell application "Safari" to add reading list item "%s"' % url]
	elif type == 'ict':
		cmd = ['/usr/bin/open', '-a', 'Safari', '-g', url]
	else:
		return 1
	return subprocess.call(cmd)

# Start HTTP server using class above to handle requests; encrypt connections
server = HTTPServer((SERVER_NAME, SERVER_PORT), rlictdRequestHandler)
server.socket = ssl.wrap_socket(server.socket, certfile='server.pem', server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)

try:
	server.serve_forever()
except KeyboardInterrupt:
	pass

