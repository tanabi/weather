# weather
Something to pull weather info off METAR and push it to a MUCK using MCP.

# To run

Make sure python3 is installed.  For ubuntu:

```
apt-get install python3 python3-pip python3-venv
```

Either set up the packages globally or in a venv.  venv is preferred if you are a python developer.  Globally is fine if you don't give a crap and just want it to be easy.

Global install:

```
sudo pip3 install -r requirements.txt
```

Venv install:

```
python3 -mvenv venv
source venv/bin/active
pip3 install -r requirements.txt
```

Set up your config.ini file.  Copy/paste this block into config.ini and edit accordingly:

```
[weather]
muck_host=hopeisland.net
muck_port=2048
use_ssl=1

mcp_key=xxxx

airport=SCIP
```

airport should be the aviation code.  For United States airports, this is the common 3 letter code with a K in front.  I.e. Raleigh-Durham NC Airport (RDU) is KRDU.

