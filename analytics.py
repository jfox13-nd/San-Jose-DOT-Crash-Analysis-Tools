#!/usr/bin/env python3

'''analytics.py: creates multiple files to represent none data about crashes on each street segment'''
__author__ = "Jack Fox"
__email__ = "jfox13@nd.edu"

import json
import csv
import sys
import psycopg2
import datetime

OUTPUTFILE = "crash_locations.json"
CSVNAME = 'CrashTable2014_2018_OpenData.csv'
USERNAME = "jfox13"
DBLOCALNAME = "dot"
OUTPUTJSON = "crash_locations.json"
OUTPUTCSV = "crash_locations.csv"
OUTPUTINJURED = "injured.csv"
OUTPUTKSI = "ksi.csv"
STREETJSON = "street_data.json"
STREET_CRASH_RELATIONSHIP = 'street_to_crash.csv'
STREETCSV = 'street_data.csv'

def db_setup() -> psycopg2.extensions.cursor:
    ''' connect to postgres database '''
    try:
        connection = psycopg2.connect(user = USERNAME,
                                    host = "127.0.0.1",
                                    port = "5432",
                                    database = DBLOCALNAME)
        cursor = connection.cursor()
        return cursor
    except:
        print("Error: Could not connect to SQL database {} as {}".format(DBLOCALNAME,USERNAME),file=sys.stderr)
        return None


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

def read_crash_csv() -> dict:
    '''Reads initial crash data csv into a dictionary, parsing out all the relevant information for each crash'''
    crash_data = dict()

    with open(CSVNAME) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line = 0
        for row in csv_reader:
            if line == 0:
                line += 1
                continue
            line += 1

            crash_id = int(row[0])
            intersection_id = int(row[5])
            direction = row[8]
            distance = row[9]
            fatal = clean_severity(row[44])
            major = clean_severity(row[45])
            moderate = clean_severity(row[46])
            minor = clean_severity(row[47])
            date = clean_date(row[2])

            if distance and distance == '0':
                direction = 'At'

            if direction == 'At':
                distance = '0'
            elif direction == 'South Of':
                direction = 'South'
            elif direction == 'East Of':
                direction = 'East'
            elif direction == 'North Of':
                direction = 'North'
            elif direction == 'West Of':
                direction = 'West'
            else:
                direction = None

            crash_data[crash_id] = dict()
            crash_data[crash_id]['intersection_id'] = intersection_id
            crash_data[crash_id]['direction'] = direction
            crash_data[crash_id]['distance'] = distance
            crash_data[crash_id]['ksi'] = calc_KSI(fatal, major)
            crash_data[crash_id]['injured'] = calc_total_injured(fatal, major, moderate, minor)
            crash_data[crash_id]['date'] = date

    return crash_data

def calc_KSI(fatal: int, major: int) -> int:
    ''' KSI calculator '''
    return fatal + major

def calc_total_injured(fatal, major, moderate, minor):
    ''' total injury calculator '''
    return fatal + major + moderate + minor

def clean_severity(n: str) -> int:
    ''' total severity calculator '''
    if not n:
        return 0
    return int(n)

def clean_date(date_str: str) -> datetime.datetime:
    ''' cleans date string into proper datetime '''
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    except:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d')

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

def feet_to_mile(feet: float) -> float:
    ''' convert feet to miles '''
    return feet / 5280.0

if __name__ == '__main__':
    cursor = db_setup()
    crash_data = read_crash_csv()
    street_crashes = dict()

    i = 0
    total_crashes = len(crash_data)
    for crash in crash_data:
        # prints progress to terminal
        i += 1
        if not i % 500:
            print('progress {:.2f}%'.format(100.0*i/total_crashes))

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


