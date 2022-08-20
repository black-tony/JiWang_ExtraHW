#!/bin/bash
# flask settings
FLASK_APP=/usr/bin/webrtc_Tony/init.py
# python FLASK_DATABASE
turnserver -c /etc/turnserver.conf -v -o -L 0.0.0.0
nohup python3 $FLASK_APP > /var/log/webrtc_Tony/error.log 2>&1 &
