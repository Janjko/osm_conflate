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

while ${run}; do
  for i in /data/*.py; do
    [ -f "$i" ] || break
	filename=$(basename -- "$i")
	mkdir -p /jsons/"${filename%.*}"/current/
    mkdir -p /jsons/"${filename%.*}"/inspected/
    mkdir -p /jsons/"${filename%.*}"/history/
	mkdir -p /rss/"${filename%.*}"/
	echo  $filename
    conflate $i -o /data/josm.osm --changes /jsons/"${filename%.*}"/current/changes.json --list_duplicates
	python3 conflate2rss/conflate2rss.py -n /jsons/"${filename%.*}"/current/changes.json -i /jsons/"${filename%.*}"/inspected/changes.json -r /rss/"${filename%.*}"/rss.xml -w /rss/"${filename%.*}"/raw_rss.json -p /jsons/"${filename%.*}"/history/ --rssurl http://46.101.158.129:8080/rss/"${filename%.*}"/rss.xml --rssauthor Janjko --rsslanguage hr --number_of_entries 10 --title "${filename%.*}"
	sleep ${PERIOD:-24h}
  done

done
