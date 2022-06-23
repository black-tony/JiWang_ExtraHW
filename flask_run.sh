#!/bin/bash
# flask settings
FLASK_APP=/home/TonyYang/ExtraHW/init.py
FLASK_DEBUG=0
FLASK_DATABASE=/home/TonyYang/ExtraHW/initdatabase.py
# python FLASK_DATABASE
turnserver -c /etc/turnserver.conf -v -o -L 0.0.0.0
nohup python3 $FLASK_APP > /home/TonyYang/ExtraHW/error.log 2>&1 &
