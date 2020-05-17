#!/usr/bin/env python3

'''
analytics.py: creates multiple files to represent data about crashes on each street segment

Output:
street_data.json: for each street segment gives all statistics and crashes
street_to_crash.csv: csv file for matching street segments to crashes
street_data.csv: basic stats for each street segment
'''
__author__ = "Jack Fox"
__email__ = "jfox13@nd.edu"

import json
import csv
import sys
import psycopg2
import datetime
from utils import db_setup, progress_bar_setup, progress_bar_increment, progress_bar_finish, clean_severity, calc_KSI, calc_total_injured, clean_date, read_crash_csv, feet_to_mile

# Files written
STREETJSON = 'data/street_data.json'
STREET_CRASH_RELATIONSHIP = 'data/street_to_crash.csv'
STREETCSV = 'data/street_data.csv'

def all_streets_from_inter(intnum: int) -> str:
    ''' return query string to get all streets connected to a given intersection '''
    query ="""
SELECT
    streetcenterlines.id
FROM streetcenterlines, intersections 
WHERE intersections.intnum = {}
    AND (frominteri = intersections.intid
        OR tointerid = intersections.intid);
"""
    return query.format(intnum)

def get_street_from_inter(intnum: int, direction: str) -> str:
    ''' return query string to get a single street given intersection and direction '''
    query ="""
SELECT
    getstreetfrominterv2(intersections.id, '{}')
FROM intersections 
WHERE intersections.intnum = {};
"""
    return query.format(direction,intnum)

def get_street_length(cursor: psycopg2.extensions.cursor, street_id: int) -> str:
    ''' street length in feet '''
    query ="""
SELECT
    ST_Length(ST_AsText(ST_LineMerge(geom)))
FROM streetcenterlines
WHERE id = {};
"""
    cursor.execute(query.format(street_id))
    record = cursor.fetchall()
    if record and record[0] and record[0][0]:
        return float(record[0][0])
    else:
        return None

def street_list_from_crash(crash_data: dict, crash: int, cursor: psycopg2.extensions.cursor) -> list:
    ''' returns a list of all streets affected by a given crash '''
    street_list = list()
    int_num = crash_data[crash]['intersection_id']
    direction = crash_data[crash]['direction']
    if not int_num or not direction:
        return street_list
    
    if direction == 'At':
        query = all_streets_from_inter(int_num)
    else:
        query = get_street_from_inter(int_num,direction)

    cursor.execute(query)
    record = cursor.fetchall()
    for street in record:
        if street[0]:
            street_list.append(int(street[0]))
    return street_list

if __name__ == '__main__':
    print("analytics.py: Gathering crash data for street segments")
    cursor, conn = db_setup()
    crash_data = read_crash_csv()
    street_crashes = dict()

    i = 0
    total_crashes = len(crash_data)
    progress_bar_setup()

    for crash in crash_data:
        # prints progress to terminal
        i += 1
        progress_bar_increment(i,total_crashes)

        # discovers all streets affected by a crash
        streets = street_list_from_crash(crash_data,crash,cursor)
        # for each street affected by a given crash, create or modify that street's dictionary entry in street_crashes to contain information on that crash
        for street in streets:

            if street not in street_crashes:
                street_crashes[street] = dict()
                street_crashes[street]['injured'] = 0
                street_crashes[street]['ksi'] = 0
                street_crashes[street]['total_crashes'] = 0
                street_crashes[street]['crashes'] = dict()
                street_crashes[street]['length'] = feet_to_mile(get_street_length(cursor,street))

            street_crashes[street]['total_crashes'] += 1
            street_crashes[street]['crashes'][crash] = dict()
            street_crashes[street]['crashes'][crash]['date'] = crash_data[crash]['date']
            street_crashes[street]['crashes'][crash]['injured'] = crash_data[crash]['injured']
            street_crashes[street]['crashes'][crash]['ksi'] = crash_data[crash]['ksi']
            street_crashes[street]['injured'] += crash_data[crash]['injured']
            street_crashes[street]['ksi'] += crash_data[crash]['ksi']
    progress_bar_finish()

    # calculate ksi/mile, injured/mile, etc. for each street in the street_crashes dictionary
    for street in street_crashes:
        if street_crashes[street]['length'] is not None:
            length = street_crashes[street]['length']
            ksi = street_crashes[street]['ksi']
            injured = street_crashes[street]['injured']
            total_crashes = street_crashes[street]['total_crashes']

            street_crashes[street]['ksi/mile'] = ksi / length
            street_crashes[street]['injured/mile'] = injured / length
            street_crashes[street]['crashes/mile'] = total_crashes / length
        else:
            street_crashes[street]['ksi/mile'] = None
            street_crashes[street]['injured/mile'] = None
            street_crashes[street]['crashes/mile'] = None

    print("analytics.py: Writing street segment data")
    # Creates CSV and JSON representations of street_crashes
    with open(STREETJSON, 'w') as f:
        f.write(json.dumps(street_crashes, default=str, indent=4))

    with open(STREETCSV, 'w') as f:
        writer = csv.writer(f,delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['id','total_crashes','injured','ksi'])
        for street in street_crashes:
            total_crashes = street_crashes[street]['total_crashes']
            injured = street_crashes[street]['injured']
            ksi = street_crashes[street]['ksi']
            writer.writerow([street, total_crashes, injured, ksi])

    with open(STREET_CRASH_RELATIONSHIP, 'w') as f:
        writer = csv.writer(f,delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['street_id','crash_id'])
        for street in street_crashes:
            for crash in street_crashes[street]['crashes']:
                writer.writerow([street,crash])


