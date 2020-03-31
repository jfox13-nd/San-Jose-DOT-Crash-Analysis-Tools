#!/usr/bin/env python3

'''connected_road_data.py'''
__author__ = "Jack Fox"
__email__ = "jfox13@nd.edu"

import json
import csv
import sys
import psycopg2
import datetime
import functools

USERNAME = "jfox13"
DBLOCALNAME = "dot"
ROADSJSON = 'roads.json'
STREETDATA = 'street_data.json'

def db_setup():
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

def get_ids(cursor, id_dict):
    ids = set()
    query ="""
SELECT
    intid
FROM streetcenterlines;
"""
    cursor.execute(query)
    for i in cursor.fetchall():
        id_dict[int(i[0])] = set()

def analyze_segment(segments, street_data):
    crash_dict = {}
    for segment in segments:
        segment = str(segment)
        if segment in street_data and 'crashes' in street_data[segment]:
            for crash in street_data[segment]['crashes']:
                crash_dict[crash] = dict()
                crash_dict[crash]['ksi'] = street_data[segment]['crashes'][crash]['ksi']
                crash_dict[crash]['injured'] = street_data[segment]['crashes'][crash]['injured']
    ksi = 0
    #functools.reduce(lambda x,y:crash_dict[x]['ksi']+crash_dict[y]['ksi'],crash_dict.keys())
    injured = 0
    #functools.reduce(lambda x,y:crash_dict[x]['injured']+crash_dict[y]['injured'],crash_dict.keys())
    for crash in crash_dict:
        if 'injured' in crash_dict[crash]:
            injured += crash_dict[crash]['injured']
        if 'ksi' in crash_dict[crash]:
            ksi += crash_dict[crash]['ksi']
    crashes = len(crash_dict)
    return ksi, injured, crashes

def get_connections(cursor):
    query ="""
SELECT
    STREETS.name,
    STREETS.id,
    STREETS.intid,
    streetcenterlines.id,
    streetcenterlines.intid,
    STREETS.a,
    STREETS.b
FROM
    (SELECT
        streetcenterlines.id,
        streetcenterlines.intid,
        streetcenterlines.frominteri as a,
        streetcenterlines.tointerid as b,
        streetcenterlines.fullname AS name
    FROM streetcenterlines
    ) AS STREETS,
    streetcenterlines
WHERE
    (streetcenterlines.frominteri = STREETS.a
    OR streetcenterlines.tointerid = STREETS.a
    OR streetcenterlines.frominteri = STREETS.b
    OR streetcenterlines.tointerid = STREETS.b
    )
    AND STREETS.name = streetcenterlines.fullname
    AND STREETS.id != streetcenterlines.id;
"""
    cursor.execute(query)
    return cursor.fetchall()

if __name__ == '__main__':
    cursor = db_setup()
    id_dict = dict()
    roads = dict()
    get_ids(cursor, id_dict)
    connections = get_connections(cursor)
    road_id = 1
    for name, ida, intida, idb, intidb, intersectiona, intersectionb in connections:
        ida = int(ida)
        idb = int(idb)
        intida = int(intida)
        intidb = int(intidb)
        intersectiona = int(intersectiona)
        intersectionb = int(intersectionb)

        #if not intida in roads:
        #    id_dict[intida] = set()
        #if not intidb in roads:
        #    id_dict[intidb] = set()
        id_dict[intida].add(intidb)
        id_dict[intidb].add(intida)
        found = False
        for i in roads:
            found = False
            if intida in roads[i]['segments']:
                roads[i]['segments'].add(intidb)
                roads[i]['intersections'].add(intersectiona)
                roads[i]['intersections'].add(intersectionb)
                found = True
                break
            if intidb in roads[i]['segments']:
                roads[i]['segments'].add(intida)
                roads[i]['intersections'].add(intersectiona)
                roads[i]['intersections'].add(intersectionb)
                found = True
                break
        if not found:
            roads[road_id] = dict()
            roads[road_id]['segments'] = set()
            roads[road_id]['intersections'] = set()
            roads[road_id]['name'] = name
            roads[road_id]['segments'].add(intida)
            roads[road_id]['segments'].add(intidb)
            roads[road_id]['intersections'].add(intersectiona)
            roads[road_id]['intersections'].add(intersectionb)
            road_id += 1

    street_data = {}
    with open(STREETDATA, 'r') as f:
        street_data = json.load(f)

    for road in roads:
        print(road)
        print(analyze_segment(roads[road]['segments'], street_data))
        break


    #with open(ROADSJSON, 'w') as f:
    #    f.write(json.dumps(roads, default=str, indent=4))
