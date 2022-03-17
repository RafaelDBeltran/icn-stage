#!/bin/bash


ssh minion@192.168.133.84 " echo "$(date +%Y%m%d%H%M.%S) 192.168.133.84" >> file.dat"