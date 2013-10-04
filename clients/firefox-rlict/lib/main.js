// This Firefox extension should post a popup menu when clicked, with options
// to load tabs from the safarid host Mac or to send current Firefox tabs to it.
// See plan.md for details; append list of specific remote tabs asynchronously.
// Remote tabs may be filed under Reading List or iCloud tabs. No such
// differentiation applies to local tabs.
//
// Authentication and encryption should be supported.
//
// Similar extensions for other popular browsers could/should be provided.
// A useful subset of the envisioned functionality could be implemented with
// generic bookmarklets that work with any [desktop] browser.
// A UNIXy (stdin/stdout URL read/write) command line utility to interact with
// safarid should also be provided, as a tool/example for other workflows. 

var tabs = require("sdk/tabs");
var data = require("sdk/self").data;
var urls = require("sdk/url");
var Request = require("sdk/request").Request;
var base64 = require("sdk/base64");
var prefs = require("sdk/simple-prefs").prefs;

// Create panel - popup "page" containing addon interface
var rlictd_panel = require("sdk/panel").Panel({
	width: 400,
	height: 400,
	contentURL: data.url('panel.html')
});

// Create widget - button that displays panel
require("sdk/widget").Widget({
	id: "rlictd-panel",
	label: "rlictd panel",
	contentURL: data.url("bookbutton.ico"),
	panel: rlictd_panel
});

// Panel display handler - invoked by FF every time panel is displayed
rlictd_panel.on("show", function() {
	
	// notify page content it is being shown
	rlictd_panel.port.emit('show');
	
	// request current tabs from rlictd
	sendData({'action': 'get', 'type': 'all'}, load_links_handler);
});

// handle response to get current tabs request placed when panel is displayed;
// validates response and relays content (tab list) to handler in content script
function load_links_handler(response) {
	if (response.status !== 200) {
		console.log("loadlinks failed");
		return;
	}
	
	if (response.json === null) {
		console.log("loadlinks 200, but null json");
		return;
	}
	
	rlictd_panel.port.emit("loadlinks", response.json);
}

// invoked when panel content script wants to send current browser tab to rlictd
rlictd_panel.port.on('send_current', function(type) {
	var data = {
		'action': 'put',
		'type': type,
		'tabs': [{
			'title': tabs.activeTab.title,
			'url': tabs.activeTab.url
		}]
	};
	sendData(data, simple_response_handler);
	rlictd_panel.hide();
});

// invoked when panel content script wants to send all browser tabs to rlictd
rlictd_panel.port.on('send_all', function(type) {
	var data = {
		'action': 'put',
		'type': type,
		'tabs': []
	};
	for each (var tab in tabs) {
		data['tabs'].push({
			'title': tab.title,
			'url': tab.url
		});
	}
	sendData(data, simple_response_handler);
	rlictd_panel.hide();
});

// do-nothing response handler for put requests
function simple_response_handler(response) {
	if (response.status !== 200) {
		console.log("sendData failed");
	}
}

// makes authenticated requests to rlictd. data is presumed JSON-compatible;
// handler is subsequently passed response to request
function sendData(data, handler) {
	var req = Request({
		url: prefs.SERVER_ADDRESS,
		headers: {
			"Authorization": "Basic " + base64.encode(prefs.AUTH_USERNAME + ":" + prefs.AUTH_PASSWORD),
			"Content-type": "application/json"
		},
		content: JSON.stringify(data),
		onComplete: handler
	});
	req.post();
};

// invoked when the panel content script wants to open a tab in local browser
rlictd_panel.port.on('visit', function(url) {
	tabs.open(url);
});
