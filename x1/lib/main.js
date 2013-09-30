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

var widgets = require("sdk/widget");
var tabs = require("sdk/tabs");
var data = require("sdk/self").data;
var urls = require("sdk/url");
var Request = require("sdk/request").Request;
var base64 = require("sdk/base64");

// Credentials for basic HTTP authentication
var AUTH_USERNAME = "foo";
var AUTH_PASSWORD = "bar";

var widget = widgets.Widget({
	id: "safarid-post",
	label: "post tabs to safarid",
	contentURL: data.url("bookbutton.ico"),
	onClick: function() {
		
		// collect tab urls to post
		var tablist = [];
		for each (var tab in tabs) {
			var taburl = urls.URL(tab.url);
			if (taburl.scheme == "https" || taburl.scheme == "http") {
				tablist.push({"Title": tab.title, "URL":tab.url});
			}
		}
		
		// send the tab list to server
		// self-signed https certificate must be previously excepted
		var tabstr = JSON.stringify(tablist);
		var tabreq = Request({
				url: "https://192.168.1.5:8081",
				headers: {
					"Authorization": "Basic " + base64.encode(AUTH_USERNAME + ":" + AUTH_PASSWORD),
					"Content-type": "application/json"
				},
				content: tabstr,
				onComplete: function(response) {
					if (response.status !== 200) {
						console.log("failed; check server");
					}
				}
		});
		tabreq.post();
	}
});
