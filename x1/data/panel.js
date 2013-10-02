addon.port.on("loadlinks", function(msg) {
	
	var ictdiv = document.getElementById('ictload');
	var rldiv = document.getElementById('rlload');
	
	while (ictdiv.lastChild) {
		ictdiv.removeChild(ictdiv.lastChild);
	}
	while (rldiv.lastChild) {
		rldiv.removeChild(rldiv.lastChild);
	}
	
	ictdiv.appendChild(makelinks(msg['tabs']['ict']));
	rldiv.appendChild(makelinks(msg['tabs']['rl']));
});


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
