#!/usr/bin/env python3
""" load_personal.py: load personal data into .personal_data """

import json
import sys
import csv
import datetime

PERSONAL_FILE = '.personal_data'
CSV_FIELDS = 9
CSV_DATE_FIELD = 8

if __name__ == '__main__':

   

    print("Please make sure you have followed all setup instructions properly before this point.\n\nPlease provide your user specific data:")
    username = input("Postgres username:").strip()
    password = input("Postgres password:").strip()
    db_name = input("Postgres database name:").strip()
    raw_crash = input("CSV with raw crash data:").strip()

    personal_data = {
        "postgres_username": username,
        "postgres_password": password,
        "postgres_database_name": db_name,
        "raw_crash_csv": raw_crash
    }

    with open(PERSONAL_FILE,'w') as fp:
        fp.write(json.dumps(personal_data, default=str, indent=4))

    # test database connection
    from utils import db_setup, clean_date
    if not db_setup():
        sys.exit(1)

    # test raw_crash_path
    try:
        with open("data/{}".format(raw_crash)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            try:
                for index, row in enumerate(csv_reader):
                    if len(row) != CSV_FIELDS:
                        print("Error: Provided CSV not properly formatted",file=sys.stdout)
                        sys.exit(1)
                    try:
                        if index != 0:
                            clean_date(row[CSV_DATE_FIELD])
                    except:
                        print("Error: Invalid date formatting in CSV",file=sys.stdout)
                        sys.exit(1)
            except:
                print("Error: Provided CSV not properly formatted",file=sys.stdout)
                sys.exit(1)
    except:
        print("Error: could not open crash CSV \"{}\"".format(raw_crash), file=sys.stdout)
        sys.exit(1)
