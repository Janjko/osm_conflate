#!/bin/bash

function sigint() {
   echo "process got SIGINT and it is exiting ..."
   run=false
}

function sigterm() {
   echo "process got SIGTERM and it is exiting ..."
   run=false
}

trap 'sigint' INT
trap 'sigterm' TERM

mkdir -p /data/current/

while ${run}; do
  conflate /data/profile.py -o /data/josm.osm --changes /data/current/changes.json
  sleep ${PERIOD:-24h}
done