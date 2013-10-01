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

var rlictd_panel = require("sdk/panel").Panel({
	width: 300,
	height: 400,
	contentURL: data.url('panel.html')/*,
	contentScriptFile: data.url('panel.js')*/
});

require("sdk/widget").Widget({
	id: "rlictd-panel",
	label: "rlictd panel",
	contentURL: data.url("bookbutton.ico"),
	panel: rlictd_panel
});

rlictd_panel.on("show", function() {
	//rlictd_panel.port.emit("show"); to notify page script it is being shown
	// when panel is display, request current list of icloud tabs from rlictd
	sendData({'action': 'get', 'type': 'all'}, load_links_handler);
});

// handle response to get-ict request; expected to contain list of tabs
function load_links_handler(response) {
	if (response.status !== 200) {
		console.log("loadlinks failed");
		return;
	}
	
	if (response.json === null) {
		console.log("loadlinks 200, but null json");
		return;
	}
	
	// format as html list; insert in panel.html (using port to panel.js if need be)
	var tabs = response.json['tabs'];
	console.log('iCloud Tabs:');
	for each (link in tabs['ict']) {
		console.log(link['url']);
	}
	console.log('Reading List:');
	for each (link in tabs['rl']) {
		console.log(link['url']);
	}
}

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

function simple_response_handler(response) {
	if (response.status !== 200) {
		console.log("sendData failed");
	}
}

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
