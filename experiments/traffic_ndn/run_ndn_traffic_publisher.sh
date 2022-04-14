#!/bin/bash
NDN_TRAFFIC_LOGFOLDER="/icn/"
nfd -c ndf.conf > /dev/null &
ndn-traffic-server ndn-traffic-server.conf
