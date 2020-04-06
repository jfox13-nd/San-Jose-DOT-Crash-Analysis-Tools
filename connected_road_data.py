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
ROADSCSV = 'roads.csv'
STREETDATA = 'street_data.json'
FEETPERMILE = 5280.0

def db_setup() -> tuple:
    ''' connect to postgres database '''
    try:
        connection = psycopg2.connect(user = USERNAME,
                                    host = "127.0.0.1",
                                    port = "5432",
                                    database = DBLOCALNAME)
        cursor = connection.cursor()
        return cursor, connection
    except:
        print("Error: Could not connect to SQL database {} as {}".format(DBLOCALNAME,USERNAME),file=sys.stderr)
        return None

def get_ids(cursor: psycopg2.extensions.cursor, id_dict: dict) -> None:
    ''' creates a dictionary with a intid key for every street segment '''
    ids = set()
    query ="""
SELECT
    intid
FROM streetcenterlines;
"""
    cursor.execute(query)
    for i in cursor.fetchall():
        id_dict[int(i[0])] = set()

def map_ids_intid(cursor: psycopg2.extensions.cursor, map_dict: dict) -> None:
    ''' creates a dictionary that maps intid to id for street segments '''
    query ="""
SELECT
    id,
    intid
FROM streetcenterlines;
"""
    cursor.execute(query)
    for i in cursor.fetchall():
        map_dict[int(i[1])] = int(i[0])

def analyze_segment(segments: list, street_data: dict, map_dict: dict) -> tuple:
    ''' return the combined ksi, injured, and total crashes for a list of street segments '''
    # create a crash_dict that holds all unique crashes (with relevant information) for the street segemnts
    crash_dict = {}

    for segment in segments:
        # convert intid to str(id) to be compatible with street data dict
        segment = str(map_dict[segment])
        if segment in street_data and 'crashes' in street_data[segment]:
            for crash in street_data[segment]['crashes']:
                crash_dict[crash] = dict()
                crash_dict[crash]['ksi'] = street_data[segment]['crashes'][crash]['ksi']
                crash_dict[crash]['injured'] = street_data[segment]['crashes'][crash]['injured']

    # calculate statistics from crash_dict
    ksi = 0
    injured = 0

    for crash in crash_dict:
        if 'injured' in crash_dict[crash]:
            injured += crash_dict[crash]['injured']
        if 'ksi' in crash_dict[crash]:
            ksi += crash_dict[crash]['ksi']
    crashes = len(crash_dict)
    return ksi, injured, crashes

def get_connections(cursor: psycopg2.extensions.cursor) -> list:
    ''' get a list of all connected street segments where each element contains information on a pair of connected segments '''
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

def get_nonconnections(cursor: psycopg2.extensions.cursor) -> list:
    ''' get a list of all connected street segments where each element contains information on a pair of connected segments '''
    query ="""
SELECT
    streetcenterlines.intid,
    streetcenterlines.frominteri,
    streetcenterlines.tointerid,
    streetcenterlines.fullname
FROM streetcenterlines
WHERE streetcenterlines.intid NOT IN
    (SELECT
        STREETS.intid
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
        AND STREETS.id != streetcenterlines.id
    );
"""
    cursor.execute(query)
    return cursor.fetchall()

def create_road_geometry(cursor: psycopg2.extensions.cursor, road: list, name) -> str:
    ''' create a linestring for a road '''

    query ="""
SELECT
    ST_LineMerge(geom) -- ST_Multi(ST_LineMerge(geom))
FROM streetcenterlines
WHERE
"""
    if road:
        query = "{}\n\tintid = {}".format(query,road[0])
    for segment in road[1:]:
        query = "{}\n\tOR intid = {}".format(query,segment)
    query = '{};'.format(query)
    
    cursor.execute(query)
    geometries = [ i[0] for i in cursor.fetchall() ]

    while len(geometries) > 1:
        query = """
SELECT ST_LineMerge( ST_Union( ST_LineMerge('{}'), ST_LineMerge('{}') ) ) ;
""".format(geometries[0],geometries[1])

        cursor.execute(query)
        geometries = geometries[1:]
        g = cursor.fetchall()[0][0]
        geometries[0] = g

    query = """
Select ST_Multi( '{}' );
""".format(geometries[0])
    cursor.execute(query)
    geometries[0] = cursor.fetchall()[0][0]

    return geometries[0]


def get_intersection_map(cursor: psycopg2.extensions.cursor) -> dict:
    ''' get all intersections associated with street segments '''
    intersection_map = dict()
    query ="""
SELECT
    intid,
    frominteri,
    tointerid,
    streetclas
FROM streetcenterlines;
"""
    cursor.execute(query)
    for i in cursor.fetchall():
        intersection_map[int(i[0])] = (int(i[1]), int(i[2]), i[3])

    return intersection_map

def create_road(intida: int, intidb: int, name: dict) -> set:
    ''' creates a set of connected street segments '''
    new_road = set((intida, intidb))
    road_expanded = True
    while road_expanded:
        road_expanded = False
        for a, b in name:
            if a in new_road and b not in new_road:
                road_expanded = True
                new_road.add(b)
            elif b in new_road and a not in new_road:
                road_expanded = True
                new_road.add(a)
    return new_road

def test_weird_data(cursor: psycopg2.extensions.cursor, roads: dict, road) -> None:
    query ="""
DROP TABLE testroad;

CREATE TABLE public.testroad (
    roadid integer PRIMARY KEY,
    geom public.geometry(MultiLineString,0), -- MultiLineString
    name character varying(125),
    ksi bigint,
    injured bigint,
    crashes bigint,
    ksi_mile float8,
    injured_mile float8,
    crashes_mile float8
);

INSERT INTO testroad( roadid, geom, name, ksi, injured, crashes, ksi_mile, injured_mile, crashes_mile)
VALUES (              {},     '{}',   '{}',   {},  {},      {},      {},       {},           {} );

SELECT UpdateGeometrySRID('public', 'testroad', 'geom', 2227);
""".format(road, 
    create_road_geometry(cursor, list(roads[road]['segments']), roads[road]['name']),
    roads[road]['name'],
    roads[road]['ksi'], 
    roads[road]['injured'],
    roads[road]['crashes'],
    roads[road]['ksi/mile'],
    roads[road]['injured/mile'],
    roads[road]['crashes/mile']
    )
    cursor.execute(query)


def road_length(cursor: psycopg2.extensions.cursor, segments: set) -> float:
    ''' returns length of entire road in miles '''
    total_length = 0.0
    if not segments:
        return total_length
    segs = list(segments)

    query ="""
SELECT
    ST_Length(ST_AsText(ST_LineMerge(geom)))
FROM streetcenterlines
WHERE intid = {}
""".format(segs[0])
    segs = segs[1:]
    for seg in segs:
        query = '{}\n\t OR intid = {}'.format(query,seg)
    query = '{};'.format(query)
    cursor.execute(query)
    
    for i in cursor.fetchall():
        total_length += float(i[0])

    return total_length / FEETPERMILE

if __name__ == '__main__':
    cursor, conn = db_setup()
    roads = dict()
    names = dict()

    # dictionary mapping of each intid to its two intersections
    intersection_map = get_intersection_map(cursor)
    # get list of all connected segments
    connections = get_connections(cursor)

    # parse connections list, create name dictionary that maps each street names to all street segment connections with that street name
    for name, ida, intida, idb, intidb, intersectiona, intersectionb in connections:
        ida = int(ida)
        idb = int(idb)
        intida = int(intida)
        intidb = int(intidb)
        intersectiona = int(intersectiona)
        intersectionb = int(intersectionb)

        if not name in names:
            names[name] = dict()
        names[name][(intida,intidb)] = (intersectiona, intersectionb)
        names[name][(intidb,intida)] = (intersectiona, intersectionb)

    # finds all roads (sets of connected street segments of the same name) with a given street name, adds this list of sets to the names dictionary
    for name in names:
        name = names[name]
        connected_segments = list()
        for intida, intidb in name:
            if len(connected_segments) == 0:
                connected_segments.append( create_road(intida,intidb,name) )
            else:
                present = False
                for connected_segment in connected_segments:
                    if intida in connected_segment or intidb in connected_segment:
                        present = True
                        break
                if not present:
                    connected_segments.append( create_road(intida,intidb,name) )
        name['roads'] = connected_segments
    
    # adds each road to the roads dictionary
    road_id = 1
    for name in names:
        streets = names[name]['roads']
        for street in streets:
            roads[road_id] = dict()
            roads[road_id]['name'] = name
            roads[road_id]['segments'] = street
            roads[road_id]['intersections']  = set(map(lambda x: intersection_map[x][0], street))
            roads[road_id]['intersections'] |= set(map(lambda x: intersection_map[x][1], street))
            road_id += 1

    # adds all street segments to the roads dictionary as single-segment roads that were not previously 
    for street in get_nonconnections(cursor):
        roads[road_id] = dict()
        roads[road_id]['name'] = street[3]
        roads[road_id]['segments'] = set( [int(street[0])] )
        roads[road_id]['intersections'] = set([int(street[1]), int(street[2])])
        road_id += 1

    street_data = {}
    map_dict = {}
    map_ids_intid(cursor, map_dict)

    with open(STREETDATA, 'r') as f:
        street_data = json.load(f)

    # calculate ksi, injury, crash statistics for each road
    for road in roads:
        roads[road]['ksi'], roads[road]['injured'], roads[road]['crashes'] = analyze_segment(roads[road]['segments'], street_data, map_dict)
        length = road_length(cursor, roads[road]['segments'])
        roads[road]['ksi/mile'] = roads[road]['ksi'] / length
        roads[road]['injured/mile'] = roads[road]['injured'] / length
        roads[road]['crashes/mile'] = roads[road]['crashes'] / length
        roads[road]['street_classification'] = set()
        for segment in roads[road]['segments']:
            roads[road]['street_classification'].add(intersection_map[segment][2])

    # write roads dictionary to JSON file
    with open(ROADSJSON, 'w') as f:
        f.write(json.dumps(roads, default=str, indent=4))

    # write roads to csv
    with open(ROADSCSV, 'w') as f:
        writer = csv.writer(f,delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['roadid','geom','name', 'street_classification', 'ksi','injured','crashes','ksi/mile','injured/mile','crashes/mile'])
        for road in roads:
            classes = list(roads[road]['street_classification'])
            if len(classes) != 1:
                road_class = 'Mixed'
            else:
                road_class = classes[0]
            writer.writerow(
                [road, 
                create_road_geometry(cursor, list(roads[road]['segments']), roads[road]['name']),
                roads[road]['name'],
                road_class,
                roads[road]['ksi'], 
                roads[road]['injured'],
                roads[road]['crashes'],
                roads[road]['ksi/mile'],
                roads[road]['injured/mile'],
                roads[road]['crashes/mile']
                ])
    conn.commit()