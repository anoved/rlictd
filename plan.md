FILES
=====

- `safarid.py` is a placeholder for the server script that runs on the host Mac.
- `x1/lib/main.js` is a placeholder for the main source code for a Firefox extension that interacts with `safarid` (loading or sending tab URLs between Firefox on whatever computer and iCloud/Reading List on the `safarid` host Mac).

MENU
====

Browser extension menu:

	X---+-Load-+-Reading List-+-All
		|      |              |
		|      |              +-<1>
		|      |              +-<2>
		|      |              +-<N>
		|      |
		|      +-iCloud Tabs--+-All
		|                     |
		|                     +-<1>
		|                     +-<2>
		|                     +-<N>
		|
		+-Send-+-Reading List-+-All
			   |			  |
			   |			  +-<1>
			   |			  +-<2>
			   |			  +-<N>
			   |
			   +-iCloud Tabs--+-all
							  |
							  +-<1>
							  +-<2>
							  +-<N>
	
Populating the "Load" branch of the tree requires retrieving data from the daemon.
I suppose if it is fast enough, this can be done as soon as the menu is opened.
Ideally, the individual tab items can be appended to the menu asynchronously
once available, so that the menu is still responsive and navigable before available.
(Albeit only with the Load-*-All options.)

SECURITY
========

Sending tabs to the remote machine will open them in (or at least add them to)
the remote host Safari browser. This could be a stupid stupid risk if insecure.
At minimum, the extension-server connection should require authentication, and
the server should probably support whitelisting in various ways. This is not
really intended as a mass market tool, so manual IP configuration is acceptable.
