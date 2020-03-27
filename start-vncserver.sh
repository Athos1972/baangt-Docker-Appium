#!/bin/bash

echo "starting VNC server ..."
export USER=root
alias python=python3
vncserver :1 -geometry 1280x800 -depth 24 && tail -F /root/.vnc/*.log
