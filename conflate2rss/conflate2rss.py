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

logging.basicConfig(level=logging.NOTSET)

class change_status(str, Enum):
    CREATE_NONE = 'CREATE_NONE'
    MODIFY_NONE = 'MODIFY_NONE'
    CREATE_MODIFY = 'CREATE_MODIFY'
    MODIFY_CREATE = 'MODIFY_CREATE'
    NONE_CREATE = 'NONE_CREATE'
    NONE_MODIFY = 'NONE_MODIFY'
    CREATE_CREATED = 'CREATE_CREATED'
    MODIFY_CREATED = 'MODIFY_CREATED'
    CREATED_CREATE = 'CREATED_CREATE'
    CREATED_MODIFY = 'CREATED_MODIFY'
    DELETE_NONE = 'DELETE_NONE'


CHANGE_STATUS = 'change_status'
ELEMENT_REF = 'element_ref'
OSM_ID = 'osm_id'
OSM_TYPE = 'osm_type'
PASS_ID = 'pass_id'
ELEMENTS = 'elements'
CREATE_ELEMENTS = 'create_elements'
MODIFY_ELEMENTS = 'modify_elements'
NEW_DATE = 'new_date'
OLD_DATE = 'old_date'

OSM_URL='https://openstreetmap.org/'

TITLE = "OSM Garden"
parser = argparse.ArgumentParser(
    description='''{}.
        Reads a profile with source data and conflates it with OpenStreetMap data.
        Produces an JOSM XML file ready to be uploaded.'''.format(TITLE))

parser.add_argument('-n', '--new', help='New file path')
parser.add_argument('-i', '--inspected', help='Output OSM XML file name path')
parser.add_argument('-r', '--rss', help='RSS XML file path')
parser.add_argument('-w', '--raw', help='Raw RSS file path')
parser.add_argument('-p', '--past', help='Folder for past changes')
parser.add_argument('-u', '--rssurl', help='Url for rss')
parser.add_argument('-a', '--rssauthor', help='Author of rss')
parser.add_argument('-l', '--rsslanguage', help='ISO language code of rss (en)')
parser.add_argument('-m', '--number_of_entries', help='Max number of RSS entries')
parser.add_argument('-t', '--title', help='Title of the RSS entries')

options = parser.parse_args()

if not os.path.isfile(options.inspected):
    if os.path.isfile(options.new):
        copyfile( options.new, options.inspected )
    sys.exit()

if not os.path.isfile(options.new):
    logging.warn('Conflator nije odradio')
    sys.exit()

logging.debug('Opening raw file')


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

newDate = newJson['osm_base']
oldDate = oldJson['osm_base']

# Brojalica za ukupni broj nedostajućih
elements_to_create=0
elements_to_modify=0
for new_element in newJson['features']:
    if new_element['properties']['action'] == 'create':
        elements_to_create += 1
    if new_element['properties']['action'] == 'modify':
        elements_to_modify += 1


for old_element in oldJson['features']:
    if 'ref_id' not in old_element['properties']:
        logging.error('Stari element https://openstreetmap.org/' + old_element['properties']['osm_type'] + '/' + str(old_element['properties']['osm_id']) + ' nema ref.')

for new_element in newJson['features']:
    if 'ref_id' not in new_element['properties']:
        logging.error('Novi element https://openstreetmap.org/' + new_element['properties']['osm_type'] + '/' + str(new_element['properties']['osm_id']) + ' nema ref.')

rss_entry = {ELEMENTS:[], PASS_ID: oldDate + '-->' + newDate, CREATE_ELEMENTS:elements_to_create, MODIFY_ELEMENTS:elements_to_modify, NEW_DATE:newDate, OLD_DATE:oldDate}

for old_element in oldJson['features']:
    new_matches = list(filter(lambda new_match: (
        new_match['properties']['ref_id'] == old_element['properties']['ref_id']), newJson['features']))
    if len(new_matches) == 0: #Ako u novom setu podataka više nema ovog upisa
        if old_element['properties']['action'] == 'create':
            rss_entry[ELEMENTS].append({CHANGE_STATUS: change_status.CREATE_NONE,
                                ELEMENT_REF: old_element['properties']['ref_id']})
        if old_element['properties']['action'] == 'modify':
            rss_entry[ELEMENTS].append({CHANGE_STATUS: change_status.MODIFY_NONE,
                                ELEMENT_REF: old_element['properties']['ref_id'], OSM_ID: old_element['properties']['osm_id'], OSM_TYPE: old_element['properties']['osm_type']})
        if old_element['properties']['action'] == 'delete':
            rss_entry[ELEMENTS].append({CHANGE_STATUS: change_status.DELETE_NONE,
                                OSM_ID: old_element['properties']['osm_id'], OSM_TYPE: old_element['properties']['osm_type']})

    for new_matched_element in new_matches:
        if old_element['properties']['action'] == 'create' and new_matched_element['properties']['action'] == 'modify':
            rss_entry[ELEMENTS].append({CHANGE_STATUS: change_status.CREATE_MODIFY,
                                ELEMENT_REF: old_element['properties']['ref_id'], OSM_ID: new_matched_element['properties']['osm_id'], OSM_TYPE: new_matched_element['properties']['osm_type']})

        if old_element['properties']['action'] == 'modify' and new_matched_element['properties']['action'] == 'create':
            rss_entry[ELEMENTS].append({CHANGE_STATUS: change_status.MODIFY_CREATE,
                                ELEMENT_REF: old_element['properties']['ref_id'], OSM_ID: old_element['properties']['osm_id'], OSM_TYPE: old_element['properties']['osm_type']})

        if old_element['properties']['action'] == 'create' and new_matched_element['properties']['action'] is None:
            rss_entry[ELEMENTS].append({CHANGE_STATUS: change_status.CREATE_CREATED,
                                ELEMENT_REF: old_element['properties']['ref_id'], OSM_ID: new_matched_element['properties']['osm_id'], OSM_TYPE: new_matched_element['properties']['osm_type']})

        if old_element['properties']['action'] == 'modify' and new_matched_element['properties']['action'] is None:
            rss_entry[ELEMENTS].append({CHANGE_STATUS: change_status.MODIFY_CREATED,
                                ELEMENT_REF: old_element['properties']['ref_id'], OSM_ID: new_matched_element['properties']['osm_id'], OSM_TYPE: new_matched_element['properties']['osm_type']})

        if old_element['properties']['action'] is None and new_matched_element['properties']['action'] == 'create':
            rss_entry[ELEMENTS].append({CHANGE_STATUS: change_status.CREATED_CREATE,
                                ELEMENT_REF: old_element['properties']['ref_id'], OSM_ID: old_element['properties']['osm_id'], OSM_TYPE: old_element['properties']['osm_type']})

        if old_element['properties']['action'] is None and new_matched_element['properties']['action'] == 'modify':
            rss_entry[ELEMENTS].append({CHANGE_STATUS: change_status.CREATED_MODIFY,
                                ELEMENT_REF: old_element['properties']['ref_id'], OSM_ID: new_matched_element['properties']['osm_id'], OSM_TYPE: new_matched_element['properties']['osm_type']})

for new_element in newJson['features']: #Ako u starom setu podataka nije bilo ovog upisa
    if not any(x['properties']['ref_id'] == new_element['properties']['ref_id'] for x in oldJson['features']):
        if new_element['properties']['action'] == 'create':
            rss_entry[ELEMENTS].append({CHANGE_STATUS: change_status.NONE_CREATE,
                           ELEMENT_REF: new_element['properties']['ref_id']})
        if new_element['properties']['action'] == 'modify':
            rss_entry[ELEMENTS].append({CHANGE_STATUS: change_status.NONE_MODIFY,
                           ELEMENT_REF: new_element['properties']['ref_id'], OSM_ID: new_element['properties']['osm_id'], OSM_TYPE: new_element['properties']['osm_type']})

print (str(len(rss_entry[ELEMENTS]))+' promjena nađeno.')

if len(rss_entry[ELEMENTS]) > 0:

# Dictionary that holds the raw rss data, from which the rss is created
    rss_raw = []

    try:
        with open(options.raw, 'r+') as json_file:
            rss_raw = json.load(json_file)
    except IOError:
        with open(options.raw, 'w+') as json_file:
            json.dump(rss_raw, json_file)

    rss_raw.append(rss_entry)

    with open(options.raw, 'w+') as fp:
        json.dump(rss_raw, fp)

    
    fg = FeedGenerator()
    fg.id(options.rssurl)
    fg.title('Garden feed')
    fg.author({'name': options.rssauthor})
    fg.subtitle('A feed of changes on the OpenStreetMap database')
    fg.link(href=options.rssurl, rel='self')
    fg.generator('OSM Garden')
    fg.lastBuildDate(newDate)
    if not options.rsslanguage:
        fg.language('en')
    else:
        fg.language(options.rsslanguage)

    for entry in rss_raw[-int(options.number_of_entries):]:
        fe = fg.add_entry()
        fe.title(options.title)
        fe.id(entry[PASS_ID])
        fe.published(entry[NEW_DATE])
        try:
            missing_elements='Nedostaje '+str(entry[CREATE_ELEMENTS])+' elemenata, i treba ih popraviti '+str(entry[MODIFY_ELEMENTS])+'.'
        except KeyError:
            missing_elements=''
        description = []
        for element in entry[ELEMENTS]:
            link_string = '<a href="' + OSM_URL + element[OSM_TYPE] + '/' + str(element[OSM_ID])+ '">' + element[ELEMENT_REF] + '</a>'
            if element[CHANGE_STATUS] in [change_status.CREATE_CREATED, change_status.MODIFY_CREATED]:
                description.append('Element ' + link_string +' ispravno ucrtan.')
            if element[CHANGE_STATUS] in [change_status.CREATED_CREATE, change_status.MODIFY_CREATE]:
                description.append('Element ' + link_string + ' obrisan, ili je izgubio osnovne tagove.')
            if element[CHANGE_STATUS] == change_status.CREATED_MODIFY:
                description.append('Elementu ' + link_string + ' pokvareni tagovi.')
            if element[CHANGE_STATUS] in [change_status.CREATE_MODIFY, change_status.NONE_MODIFY]:
                description.append('Element ' + link_string + ' ucrtan, ali sa lošim tagovima.')
            if element[CHANGE_STATUS] == change_status.NONE_CREATE:
                description.append('Element ' + link_string + ' dodan u ulazni dataset.')
            description.append(missing_elements)
        fe.description(' '.join(description))

    fg.rss_file(options.rss)

os.rename( options.inspected, os.path.join( options.past,'inspected_'+newDate.replace(':','')+'.json' ) )
os.rename( options.new, options.inspected )
