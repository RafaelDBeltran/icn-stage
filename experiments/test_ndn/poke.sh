#!/bin/bash

nfd-start

sleep 5s

echo 'Message: HELLO WORLD' | ndnpoke /demo/hello

sleep 10s

nfd-stop