#!/usr/bin/env python3

'''crash_location.py: script to produce json file of all crash coordinates'''
__author__ = "Jack Fox"
__email__ = "jfox13@nd.edu"

import json
import csv
import psycopg2

CSVNAME = 'CrashTable2014_2018_OpenData.csv'
USERNAME = "jfox13"
DBLOCALNAME = "dot"
OUTPUTJSON = "crash_locations.json"
OUTPUTCSV = "crash_locations.csv"
OUTPUTINJURED = "injured.csv"
OUTPUTKSI = "ksi.csv"

def db_setup() -> None:
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

def read_crash_csv():
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

    #s = set()
    #for c in crash_data:
    #    s.add(crash_data[c]['direction'])
    #print(s)

    return crash_data            
    
def add_gps(d,crash, cursor):
    if not d[crash]['distance'] or not d[crash]['direction']:
        d[crash]['int_id'] = None
        d[crash]['longitude'] = None
        d[crash]['latitude'] = None
        return

    try:
        distance = int(d[crash]['distance'])
    except:
        d[crash]['int_id'] = None
        d[crash]['longitude'] = None
        d[crash]['latitude'] = None
        return

    direction = d[crash]['direction']
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
    """.format(direction,distance,d[crash]['intersection_id'])

    cursor.execute(query)
    record = cursor.fetchall()

    if not record or not record[0] or not record[0][0] or not record[0][1] or not record[0][2]:
        d[crash]['int_id'] = None
        d[crash]['longitude'] = None
        d[crash]['latitude'] = None
        return

    d[crash]['int_id'] = record[0][0]
    d[crash]['latitude'] = record[0][1]
    d[crash]['longitude'] = record[0][2]

def calc_KSI(fatal, major):
    return fatal + major

def calc_total_injured(fatal, major, moderate, minor):
    return fatal + major + moderate + minor

def clean_severity(n):
    if not n:
        return 0
    return int(n)

if __name__ == '__main__':
    cursor = db_setup()
    d = read_crash_csv()
    good = 0
    bad = 0
    print("READ DONE")
    length = len(d)
    i = 0
    for crash in d:
        i += 1
        if not i % 1000:
            print('progress {}'.format(i/length))
        add_gps(d,crash,cursor)

    for crash in d:
        if d[crash]['longitude']:
            good += 1
        else:
            bad += 1
    print("good = {} \n bad = {}".format(good,bad))

    with open(OUTPUTJSON, 'w') as f:
        f.write(json.dumps(d,indent=4))
    
    with open(OUTPUTCSV,'w') as f:
        writer = csv.writer(f,delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(['crash_id','intersection_id','int_num','direction','distance','latitude','longitude'])
        for crash in d:
            writer.writerow([
                crash,
                d[crash]['int_id'],
                d[crash]['intersection_id'],
                d[crash]['direction'],
                d[crash]['distance'],
                d[crash]['latitude'],
                d[crash]['longitude']
            ])

    with open(OUTPUTKSI, 'w') as f_ksi, open(OUTPUTINJURED, 'w') as f_injured :
        writer_ksi = csv.writer(f_ksi,delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer_injured = csv.writer(f_injured,delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        ksi_id = 1
        injured_id = 1

        writer_ksi.writerow(['id','latitude','longitude'])
        writer_injured.writerow(['id','latitude','longitude'])

        for crash in d:
            for _ in range(d[crash]['ksi']):
                writer_ksi.writerow([
                    ksi_id,
                    d[crash]['latitude'],
                    d[crash]['longitude']
                ])
                ksi_id += 1
            for _ in range(d[crash]['injured']):
                writer_injured.writerow([
                    injured_id,
                    d[crash]['latitude'],
                    d[crash]['longitude']
                ])
                injured_id += 1
