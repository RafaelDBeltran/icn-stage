#!/bin/bash



python daemon_controller.py restart

sleep 2

python 30_trackerlens.py reset
