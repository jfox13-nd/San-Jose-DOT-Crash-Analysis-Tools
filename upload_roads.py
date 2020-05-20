#!/usr/bin/env python3

'''
upload_roads.py: upload the data in roads.csv to postgres with table name 'roads'
'''
__author__ = "Jack Fox"
__email__ = "jfox13@nd.edu"

import sys
import csv
import psycopg2
import pathlib
from utils import db_setup

ROADS_COLUMNS = 11

def upload_data(cursor: psycopg2.extensions.cursor, csv_path: str) -> None:
    ''' execute SQL to upload roads.csv to postgres '''
    query = """
DROP TABLE IF EXISTS roads;

CREATE TABLE public.roads (
    roadid integer PRIMARY KEY,
    geom public.geometry(MultiLineString,0),
    name character varying(125),
    street_classification character varying(125),
    relevant_road BOOL,
    ksi bigint,
    injured bigint,
    crashes bigint,
    ksi_mile float8,
    injured_mile float8,
    crashes_mile float8
);

COPY roads(roadid, geom, name, street_classification, relevant_road, ksi, injured, crashes, ksi_mile, injured_mile, crashes_mile) FROM '{}' DELIMITER ',' CSV HEADER;

SELECT UpdateGeometrySRID('public', 'roads', 'geom', 2227);

""".format(csv_path)
    cursor.execute(query)

if __name__ == '__main__':
    cursor, conn = db_setup()

    csv_path = '{}/data/roads.csv'.format(pathlib.Path(__file__).parent.absolute())

    try:
        csv_file = open('data/roads.csv', 'r')
    except:
        print("Error: Could not open roads.csv",file=sys.stdout)
        sys.exit(1)
    
    try:
        csv_reader = csv.reader(csv_file, delimiter=',')
    except:
        print("Error: roads.csv improperly formatted",file=sys.stdout)
        sys.exit(1)

    for row in csv_reader:
        if len(row) != ROADS_COLUMNS:
            print("Error: roads.csv improperly formatted\n\tInvalid number of columns",file=sys.stdout)
            sys.exit(1)
    csv_file.close()

    upload_data(cursor,csv_path)
    conn.commit()