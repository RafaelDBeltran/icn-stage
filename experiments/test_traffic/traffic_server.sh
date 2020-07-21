#!/bin/bash
nfd-start

sleep 5s

ndn-traffic-server ndn-traffic-server.conf
