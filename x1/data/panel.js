// Interaction with the panel HTML is performed by this content script.

// Invoked by addon after panel is displayed, once current remote tab data is
// available. Updates panel content with links to current remote tabs.
addon.port.on("loadlinks", function(msg) {
	
	var ictdiv = document.getElementById('ictload');
	var rldiv = document.getElementById('rlload');
	
	// remove any previously-appended tab link lists
	while (ictdiv.lastChild) {
		ictdiv.removeChild(ictdiv.lastChild);
	}
	while (rldiv.lastChild) {
		rldiv.removeChild(rldiv.lastChild);
	}
	
	// append lists of tab links for each remote collection
	ictdiv.appendChild(makelinks(msg['tabs']['ict']));
	rldiv.appendChild(makelinks(msg['tabs']['rl']));
});

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
