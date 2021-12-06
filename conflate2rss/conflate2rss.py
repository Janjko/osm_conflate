#!/usr/bin/python

from json import encoder
import sys
from datetime import datetime, tzinfo
import os
from shutil import copyfile
import argparse
import json
import jsondiff as jd
from jsondiff import diff
from feedgen.feed import FeedGenerator
from enum import Enum
import logging

class change_status(str, Enum):
    CREATE_NONE = 'CREATE_NONE'
    MODIFY_NONE = 'MODIFY_NONE'
    CREATE_MODIFY = 'CREATE_MODIFY'
    MODIFY_CREATE = 'MODIFY_CREATE'
    NONE_CREATE = 'NONE_CREATE'
    NONE_MODIFY = 'NONE_MODIFY'


CHANGE_STATUS = 'change_status'
ELEMENT_REF = 'element_ref'
OSM_ID = 'osm_id'
PASS_ID = 'pass_id'

# Dictionary that holds the raw rss data, from which the rss is created
rss_raw = []

TITLE = "OSM Garden"
parser = argparse.ArgumentParser(
    description='''{}.
        Reads a profile with source data and conflates it with OpenStreetMap data.
        Produces an JOSM XML file ready to be uploaded.'''.format(TITLE))

parser.add_argument('-n', '--new', help='New file path')
parser.add_argument('-i', '--inspected', help='Output OSM XML file name path')
parser.add_argument('-r', '--rss', type=argparse.FileType('w'), help='RSS XML file path')
parser.add_argument('-w', '--raw', help='Raw RSS file path')
parser.add_argument('-p', '--past', help='Folder for past changes')
parser.add_argument('-u', '--rssurl', help='Url for rss')
parser.add_argument('-a', '--rssauthor', help='Author of rss')
parser.add_argument('-l', '--rsslanguage', help='ISO language code of rss (en)')
#options = parser.parse_args(["-n", "C:\\Users\\Janko\\source\\garden\\jsons\\current\\changes.json", "-i",
#                           "C:\\Users\\Janko\\source\\garden\\jsons\\inspected\\changes.json", "-r", "C:\\Users\\Janko\\source\\garden\\rss\\rss.xml",
#                           "-p", "C:\\Users\\Janko\\source\\garden\\jsons\\history", "-w", "C:\\Users\\Janko\\source\\garden\\rss\\rss.json"])

options = parser.parse_args()

fg = FeedGenerator()
fg.id(options.rssurl)
fg.title('Garden feed')
fg.author({'name': options.rssauthor})
fg.subtitle('A feed of changes on the OpenStreetMap database')
fg.link(href=options.rssurl, rel='self')
if not options.rsslanguage:
    fg.language('en')
else:
    fg.language(options.rsslanguage)

if not os.path.isfile(options.inspected):
    if os.path.isfile(options.new):
        copyfile( options.new, options.inspected )
    sys.exit()

if not os.path.isfile(options.new):
    logging.warn('Conflator nije odradio')
    sys.exit()

pass_id = datetime.today().strftime('%Y-%m-%d-%H-%M')

logging.debug('Opening raw file')

try:
    with open(options.raw, 'r+') as json_file:
        rss_raw = json.load(json_file)
except IOError:
    with open(options.raw, 'w+') as json_file:
        json.dump(rss_raw, json_file)

with open(options.new, encoding='utf-8') as new_json_file:
    try:
        newJson = json.load(new_json_file)
    except:
        logging.error('New file is in a wrong format.')
        os.remove(options.new)
        sys.exit()

with open (options.inspected, encoding='utf-8') as old_json_file:
    try:
        oldJson = json.load(old_json_file)
    except:
        logging.error('Old file is in a wrong format.')
        os.remove(options.inspected)
        sys.exit()

for old_element in oldJson['features']:
    new_matches = list(filter(lambda new_match: (
        new_match['properties']['ref_id'] == old_element['properties']['ref_id']), newJson['features']))
    if len(new_matches) == 0: #Ako u novom setu podataka više nema ovog upisa
        if old_element['properties']['action'] == 'create':
            rss_raw.append({CHANGE_STATUS: change_status.CREATE_NONE,
                                ELEMENT_REF: old_element['properties']['ref_id'],
                                PASS_ID: pass_id})
        if old_element['properties']['action'] == 'modify':
            rss_raw.append({CHANGE_STATUS: change_status.MODIFY_NONE,
                                ELEMENT_REF: old_element['properties']['ref_id'], OSM_ID: old_element['properties']['osm_id'],
                                PASS_ID: pass_id})

    for new_matched_element in new_matches:
        if old_element['properties']['action'] == 'create' and new_matched_element['properties']['action'] == 'modify':
            rss_raw.append({CHANGE_STATUS: change_status.CREATE_MODIFY,
                                ELEMENT_REF: old_element['properties']['ref_id'], OSM_ID: new_matched_element['properties']['osm_id'], PASS_ID: pass_id})

        if old_element['properties']['action'] == 'modify' and new_matched_element['properties']['action'] == 'create':
            rss_raw.append({CHANGE_STATUS: change_status.MODIFY_CREATE,
                                ELEMENT_REF: old_element['properties']['ref_id'], OSM_ID: old_element['properties']['osm_id'], PASS_ID: pass_id})

for new_element in newJson['features']: #Ako u starom setu podataka nije bilo ovog upisa
    if not any(x['properties']['ref_id'] == new_element['properties']['ref_id'] for x in oldJson['features']):
        if new_element['properties']['action'] == 'create':
            rss_raw.append({CHANGE_STATUS: change_status.NONE_CREATE,
                           ELEMENT_REF: new_element['properties']['ref_id'], PASS_ID: pass_id})
        if new_element['properties']['action'] == 'modify':
            rss_raw.append({CHANGE_STATUS: change_status.NONE_MODIFY,
                           ELEMENT_REF: new_element['properties']['ref_id'], OSM_ID: new_element['properties']['osm_id'], PASS_ID: pass_id})


with open(options.raw, 'w+') as fp:
    json.dump(rss_raw, fp)

for entry in rss_raw:
    fe = fg.add_entry()
    if entry[CHANGE_STATUS] == change_status.CREATE_NONE or entry[CHANGE_STATUS] == change_status.MODIFY_NONE:
        fe.title("Element ispravno ucrtan.")
        fe.description('Ispravno ucrtan element ' +
                       old_element['properties']['ref_id'])
        fe.id(entry[PASS_ID])
    if entry[CHANGE_STATUS] == change_status.NONE_CREATE or entry[CHANGE_STATUS] == change_status.MODIFY_CREATE:
        fe.title("Element obrisan!")
        fe.description('Element ' +
                       old_element['properties']['ref_id'] + ' obrisan, ili je izgubio osnovne tagove.')
        fe.id(entry[PASS_ID])
    if entry[CHANGE_STATUS] == change_status.NONE_MODIFY:
        fe.title("Elementu pokvareni tagovi.")
        fe.description('Elementu ' +
                       old_element['properties']['ref_id'] + ' pokvareni tagovi.')
        fe.id(entry[PASS_ID])
    if entry[CHANGE_STATUS] == change_status.CREATE_MODIFY:
        fe.title("Element ucrtan, ali sa lošim tagovima.")
        fe.description('Element ' +
                       old_element['properties']['ref_id'] + ' ucrtan, ali sa lošim tagovima.')
        fe.id(entry[PASS_ID])

fg.rss_file(options.rss.name)

os.rename( options.inspected, os.path.join( options.past,'inspected_'+pass_id+'.json' ) )
os.rename( options.new, options.inspected )

