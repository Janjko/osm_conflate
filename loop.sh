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

mkdir -p /jsons/current/
mkdir -p /jsons/inspected/
mkdir -p /jsons/history/

while ${run}; do
  conflate /data/profile.py -o /data/josm.osm --changes /jsons/current/changes.json --list_duplicates
  python3 conflate2rss/conflate2rss.py -n /jsons/current/changes.json -i /jsons/inspected/changes.json -r /rss/rss.xml -w /rss/raw_rss.json -p /jsons/history/ --rssurl http://46.101.158.129:8080/rss/rss.xml --rssauthor Janjko --rsslanguage hr --number_of_entries 10
  sleep ${PERIOD:-24h}
done
