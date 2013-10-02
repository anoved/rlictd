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
	var icth2 = document.createElement('h2');
	icth2.appendChild(document.createTextNode('iCloud Tabs'));
	ictd.appendChild(icth2);
	for (var key in tablists) {
		var dh3 = document.createElement('h3');
		dh3.appendChild(document.createTextNode(key))
		ictd.appendChild(dh3);		
		ictd.appendChild(makelinks(tablists[key]));
	}
}

function makeRlLinks(rld, tablist) {
	var h2 = document.createElement('h2');
	h2.appendChild(document.createTextNode('Reading List'));
	rld.appendChild(h2);
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

