#!/usr/bin/env python3

'''utils.py'''
__author__ = "Jack Fox"
__email__ = "jfox13@nd.edu"

import json
import sys
import psycopg2

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