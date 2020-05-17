#!/usr/bin/env python3

'''utils.py'''
__author__ = "Jack Fox"
__email__ = "jfox13@nd.edu"

import json
import sys
import psycopg2
import csv
import datetime

USERNAME = ""
PASSWORD = ""
DBLOCALNAME = ""
RAWCRASHCSV = ""

FEETPERMILE = 5280.0
PROGRESS_BAR_WIDTH = 40

def db_setup() -> tuple:
    ''' connect to postgres database '''
    try:
        connection = psycopg2.connect(user = USERNAME,
                                    password = PASSWORD,
                                    host = "127.0.0.1",
                                    port = "5432",
                                    database = DBLOCALNAME)
        cursor = connection.cursor()
        return cursor, connection
    except:
        print("Error: Could not connect to SQL database {} as {}".format(DBLOCALNAME,USERNAME),file=sys.stderr)
        return None

with open(".personal_data", 'r') as f:
    personal_data = json.load(f)
    USERNAME = personal_data["postgres_username"]
    PASSWORD = personal_data["postgres_password"]
    DBLOCALNAME = personal_data["postgres_database_name"]
    RAWCRASHCSV = "data/{}".format(personal_data["raw_crash_csv"])

def progress_bar_setup() -> None:
    ''' setup for progress bar '''
    sys.stdout.write("[%s]" % (" " * PROGRESS_BAR_WIDTH))
    sys.stdout.flush()
    sys.stdout.write("\b" * (PROGRESS_BAR_WIDTH+1)) # return to start of line, after '['

def progress_bar_increment(i: int, total: int) -> None:
    ''' increment progress bar if needed given the total tasks that need to be done and the amount already completed '''
    increment = total / PROGRESS_BAR_WIDTH
    if i > 1 and int((i-1)/increment) < int((i)/increment):
        sys.stdout.write("-")
        sys.stdout.flush()

def progress_bar_finish() -> None:
    ''' end progress bar '''
    sys.stdout.write("]\n")
    sys.stdout.flush()

def clean_severity(n: str) -> int:
    ''' total severity calculator '''
    if not n:
        return 0
    return int(n)

def read_crash_csv() -> dict:
    '''Reads initial crash data csv into a dictionary, parsing out all the relevant information for each crash'''
    crash_data = dict()

    with open(RAWCRASHCSV) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line = 0
        for row in csv_reader:
            if line == 0:
                line += 1
                continue
            line += 1

            crash_id = row[0]
            intersection_id = int(row[1])
            direction = row[2]
            distance = row[3]
            fatal = clean_severity(row[4])
            major = clean_severity(row[5])
            moderate = clean_severity(row[6])
            minor = clean_severity(row[7])
            date = clean_date(row[8])

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

def clean_date(date_str: str) -> datetime.datetime:
    ''' cleans date string into proper datetime '''
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    except:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d')

def calc_KSI(fatal: int, major: int) -> int:
    ''' KSI calculator '''
    return fatal + major

def calc_total_injured(fatal, major, moderate, minor):
    ''' total injury calculator '''
    return fatal + major + moderate + minor

def feet_to_mile(feet: float) -> float:
    ''' convert feet to miles '''
    return feet / FEETPERMILE