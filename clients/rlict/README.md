# rlict

`rlict` is a stand-alone command-line `rlictd` client. It submits URLs read from `stdin` (one per line) and prints retrieved URLs to `stdout` (also one per line). The target collection (Reading List or iCloud Tabs) is specified by command line switches. Server information (ip, port, auth, etc) may be given as options as well. Defaults for command line parameters are read from a config file, if available.
