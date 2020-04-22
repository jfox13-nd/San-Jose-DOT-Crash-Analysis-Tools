#!/usr/bin/env python3

'''connected_road_data.py'''
__author__ = "Jack Fox"
__email__ = "jfox13@nd.edu"

USERNAME = "jfox13"
DBLOCALNAME = "dot"

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

with open(".personal_data", 'r') as f:
    personal_data = json.load(f)
    USERNAME = personal_data["postgres_username"]
    DBLOCALNAME = personal_data["postgres_database_name"]