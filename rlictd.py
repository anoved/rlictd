#!/usr/bin/python

from ConfigParser import SafeConfigParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urlparse import urlparse
from base64 import b64decode
from subprocess import call
import os
import ssl
import json
import socket

from readinglistlib import ReadingListReader
from icloudtabslib import iCloudTabsReader

class rlictdConfig():
	def __init__(self, path=''):
		
		# search for config file first at the path passed to this constructor
		# (if any), then in current directory, and lastly in user's home dir.
		files = ['rlictd.cfg', os.path.expanduser('~/.rlictd.cfg')]
		if path != '':
			files.insert(0, path)
			
		cp = SafeConfigParser()
		cp.read(files)
		
		self.ips = cp.get('rlictd', 'IP_WHITELIST').split()
		self.username = cp.get('rlictd', 'AUTH_USERNAME')
		self.password = cp.get('rlictd', 'AUTH_PASSWORD')
		self.port = cp.getint('rlictd', 'SERVER_PORT')

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
		if len(config.ips) > 0 and self.client_address[0] not in config.ips:
			self.send_error(403, "Disallowed IP address")
			return False
		
		if (config.username != '') and (config.password != ''):
						
			# require authorization
			if 'Authorization' not in self.headers:
				self.send_error(401, "Authorization required")
				return False
		
			# get authorization values
			authtoken = self.headers['Authorization'].split(' ', 1)[1]
			username, password = b64decode(authtoken).split(':', 1)
		
			# require correct authentication
			if (username != config.username) or (password != config.password):
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
			response = {'ict': [], 'rl': []}
			if type == 'rl':
				response['rl'] = formatResponseRL(ReadingListReader().read(ascending=False))
			elif type == 'ict': 
				response['ict'] = formatResponseICT(iCloudTabsReader().tabs)
			elif type == 'all': 
				response['rl'] = formatResponseRL(ReadingListReader().read(ascending=False))
				response['ict'] = formatResponseICT(iCloudTabsReader().tabs)
			
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

# 'tabs' is list of Reading List item dicts as returned by ReadingListReader
# returns list formatted as expected by rlictd clients (currently the same)
def formatResponseRL(tabs):
	urls = []
	for tab in tabs:
		urls.append({'title': tab['title'], 'url': tab['url']})
	return urls

# 'tabs' is list of iCloud Tabs dicts as returned by iCloudTabsReader
# returns dict with iCloud device names as keys. dict values are lists of dicts
# representing the tabs open on each device.
def formatResponseICT(tabs):
	devices = list(set([tab['device'] for tab in tabs]))
	results = {}
	for device in devices:
		results[device] = [{'title': tab['title'], 'url': tab['url']} for tab in tabs if tab['device'] == device]
	return results

# deliver url to collection identified by type, which determines command
# returns command exit status: 0 on success, nonzero otherwise (should log details)
def putUrl(rawUrl, type):
	
	parts = urlparse(rawUrl);
	if ((parts.scheme != 'http') and (parts.scheme != 'https')) or (parts.netloc == ''):
		return 1
	url = parts.geturl()
	
	if type == 'rl':
		cmd = ['/usr/bin/osascript', '-e', 'tell application "Safari" to add reading list item "%s"' % url]
	elif type == 'ict':
		cmd = ['/usr/bin/open', '-a', 'Safari', '-g', url]
	else:
		return 1
	return call(cmd)


config = rlictdConfig()

# Start HTTP server using class above to handle requests; encrypt connections
address = socket.gethostbyname(socket.gethostname())
server = HTTPServer((address, config.port), rlictdRequestHandler)
server.socket = ssl.wrap_socket(server.socket, certfile='server.pem', server_side=True, ssl_version=ssl.PROTOCOL_TLSv1)
print "listening on %s:%s" % (address, config.port)

try:
	server.serve_forever()
except KeyboardInterrupt:
	pass

