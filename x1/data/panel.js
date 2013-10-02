// Interaction with the panel HTML is performed by this content script.

// Invoked by addon after panel is displayed, once current remote tab data is
// available. Updates panel content with links to current remote tabs.
addon.port.on("loadlinks", function(msg) {
	
	var ictdiv = document.getElementById('ict');
	var rldiv = document.getElementById('rl');
	
	// remove any previously-appended tab link lists
	while (ictdiv.lastChild) {
		ictdiv.removeChild(ictdiv.lastChild);
	}
	while (rldiv.lastChild) {
		rldiv.removeChild(rldiv.lastChild);
	}
	
	makeIctLinks(ictdiv, msg['tabs']['ict']);
	makeRlLinks(rldiv, msg['tabs']['rl']);
});

function makeIctLinks(ictd, tablists) {
	ictd.innerHTML = '<h2>iCloud Tabs</h2>';
	ictd.innerHTML += '<p><a href="#" onclick="addon.port.emit(\'send_current\', \'ict\');">Add current tab</a> or <a href="#" onclick="addon.port.emit(\'send_all\', \'ict\');">add all tabs</a>.</p>';
	for (var key in tablists) {
		var dh3 = document.createElement('h3');
		dh3.appendChild(document.createTextNode(key))
		ictd.appendChild(dh3);		
		ictd.appendChild(makelinks(tablists[key]));
	}
}

function makeRlLinks(rld, tablist) {
	rld.innerHTML = '<h2>Reading List</h2>';
	rld.innerHTML += '<p><a href="#" onclick="addon.port.emit(\'send_current\', \'rl\');">Add current tab</a> or <a href="#" onclick="addon.port.emit(\'send_all\', \'rl\');">add all tabs</a>.</p>';
	rld.appendChild(makelinks(tablist));
}

// Return an element tree containing a list of tab links
function makelinks(tablist) {
	var dUl = document.createElement('ul');
	for (var i = 0; i < tablist.length; i++) {
		var dLi = document.createElement('li');
		var dLink = document.createElement('a');
		dLink.setAttribute('href', '#');
		dLink.setAttribute('onclick', "addon.port.emit('visit', '" + tablist[i]['url'] + "');");
		var dText = document.createTextNode(tablist[i]['title']);
		dLink.appendChild(dText);
		dLi.appendChild(dLink);
		dUl.appendChild(dLi);
	}
	return dUl;
}

