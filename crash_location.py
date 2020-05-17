#!/usr/bin/env python3

'''
crash_location.py: script to produce output files of all crash coordinates

Outputs:
crash_locations.json: for each crash will include actual coordinates, intersection relative location and direction, ksi, injured
crash_locations.csv: the longitude and lattitude for each crash
injured.csv: the longitude and lattitude of each injury
ksi.csv: the longitude and lattitude of each injury
'''
__author__ = "Jack Fox"
__email__ = "jfox13@nd.edu"

import json
import csv
import psycopg2
from utils import db_setup, progress_bar_setup, progress_bar_increment, progress_bar_finish, clean_severity, read_crash_csv, calc_KSI, calc_total_injured

# Files written
OUTPUTJSON = "data/crash_locations.json"
OUTPUTCSV = "data/crash_locations.csv"
OUTPUTINJURED = "data/injured.csv"
OUTPUTKSI = "data/ksi.csv"  
    
def add_gps(crash_data: dict, crash: str, cursor: psycopg2.extensions.cursor) -> None:
    ''' '''
    if not crash_data[crash]['distance'] or not crash_data[crash]['direction']:
        crash_data[crash]['int_id'] = None
        crash_data[crash]['longitude'] = None
        crash_data[crash]['latitude'] = None
        return

    try:
        distance = int(crash_data[crash]['distance'])
    except:
        crash_data[crash]['int_id'] = None
        crash_data[crash]['longitude'] = None
        crash_data[crash]['latitude'] = None
        return

    direction = crash_data[crash]['direction']
    if direction == 'At':
        direction = 'South'
    
    query ="""
    SELECT
    Q.id,
    pointy(Q.g) AS y,
    pointx(Q.g) AS x 
    FROM (SELECT 
        id,
        findcrashlocation(id, '{}', {}) AS g
    FROM intersections
    WHERE
    intnum = {}
    ) AS Q;
    """.format(direction,distance,crash_data[crash]['intersection_id'])

    cursor.execute(query)
    record = cursor.fetchall()

    if not record or not record[0] or not record[0][0] or not record[0][1] or not record[0][2]:
        crash_data[crash]['int_id'] = None
        crash_data[crash]['longitude'] = None
        crash_data[crash]['latitude'] = None
        return

    crash_data[crash]['int_id'] = record[0][0]
    crash_data[crash]['latitude'] = record[0][1]
    crash_data[crash]['longitude'] = record[0][2]

if __name__ == '__main__':
    print("crash_location.py: Producing crash locations point outputs")
    cursor, conn = db_setup()
    crash_data = read_crash_csv()

    total_crashes = len(crash_data)
    i = 0
    progress_bar_setup()
    for crash in crash_data:
        i += 1
        progress_bar_increment(i,total_crashes)
        add_gps(crash_data,crash,cursor)
    progress_bar_finish()

    location_found = 0
    location_not_found = 0
    for crash in crash_data:
        if crash_data[crash]['longitude']:
            location_found += 1
        else:
            location_found += 1
    print("crash_location.py:\n\tCrash locations found = {} \n\t Crash locations not found = {}".format(location_found,location_not_found))

    print("crash_location.py: Writing crash locations point outputs")

    with open(OUTPUTJSON, 'w') as f:
        f.write(json.dumps(crash_data, default=str, indent=4))
    
    with open(OUTPUTCSV,'w') as f:
        writer = csv.writer(f,delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(['crash_id','intersection_id','int_num','direction','distance','latitude','longitude'])
        for crash in crash_data:
            writer.writerow([
                crash,
                crash_data[crash]['int_id'],
                crash_data[crash]['intersection_id'],
                crash_data[crash]['direction'],
                crash_data[crash]['distance'],
                crash_data[crash]['latitude'],
                crash_data[crash]['longitude']
            ])

    with open(OUTPUTKSI, 'w') as f_ksi, open(OUTPUTINJURED, 'w') as f_injured :
        writer_ksi = csv.writer(f_ksi,delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer_injured = csv.writer(f_injured,delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        ksi_id = 1
        injured_id = 1

        writer_ksi.writerow(['id','latitude','longitude'])
        writer_injured.writerow(['id','latitude','longitude'])

        for crash in crash_data:
            for _ in range(crash_data[crash]['ksi']):
                writer_ksi.writerow([
                    ksi_id,
                    crash_data[crash]['latitude'],
                    crash_data[crash]['longitude']
                ])
                ksi_id += 1
            for _ in range(crash_data[crash]['injured']):
                writer_injured.writerow([
                    injured_id,
                    crash_data[crash]['latitude'],
                    crash_data[crash]['longitude']
                ])
                injured_id += 1
