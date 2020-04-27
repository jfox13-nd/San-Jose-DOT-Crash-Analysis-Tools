#!/usr/bin/env python3
""" load_personal.py: load personal data into .personal_data """

import json
import sys
import csv
PERSONAL_FILE = '.personal_data'
CSV_FIELDS = 49

if __name__ == '__main__':

   

    print("Please make sure you have followed all setup instructions properly before this point.\n\nPlease provide your user specific data:")
    username = input("Postgres username:").strip()
    db_name = input("Postgres database name:").strip()
    raw_crash = "data/{}".format(input("CSV with raw crash data:").strip())

    personal_data = {
        "postgres_username": username,
        "postgres_database_name": db_name,
        "raw_crash_csv": raw_crash
    }

    with open(PERSONAL_FILE,'w') as fp:
        fp.write(json.dumps(personal_data, default=str, indent=4))

    # test database connection
    from utils import db_setup
    if not db_setup():
        sys.exit(1)

    # test raw_crash_path
    try:
        with open(raw_crash) as csv_file:
            try:
                csv_reader = csv.reader(csv_file, delimiter=',')
                for row in csv_reader:
                    if len(row) != CSV_FIELDS:
                        print("1Error: Provided CSV not properly formatted",file=sys.stdout)
                        sys.exit(1)
            except:
                print("Error: Provided CSV not properly formatted",file=sys.stdout)
                sys.ext(1)
    except:
        print("Error: could not open crash CSV \"{}\"".format(raw_crash), file=sys.stdout)
        sys.exit(1)
