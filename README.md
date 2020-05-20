# San Jose Crash Data Analysis Tools

## Description
These tools are for use by San Jose Vision Zero within the San Jose DOT. Given correctly formatted data on crash locations these scipts will infer the GPS coordinates of those crashes and conduct further analysis from that data. Multiple CSV and JSON files will be output that will describe the relationships between crashes, street segments, and roads.

## Terminology
* Street Segment
    * The geometry of a single feature in the DOT's "Street Centerlines" map of San Jose
* Road
    * A collection of contiguous street segments with the same name and DOT street classification
    * Every street segment within a road must touch territory under the jurisdiction of the city of San Jose
        * The "munileft" or the "muniright" field for that street segment must have a value of "sj"
* KSI
    * A traffic crash where an involved party was killed or severly injured

## Setup

### 1. Clone this repository
```bash
git clone https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools.git
```

### 2. Clone and setup the [San-Jose-DOT-Crash-Locator](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator) repository
Make sure to follow all setup instructions and confirm that your postgres database is running before proceeding.
You do not need to clone the [San-Jose-DOT-Crash-Locator Repo](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator) into this repository.
```bash
git clone https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator.git
```

### 3. Install all relevant Python3 modules
```bash
pip install -r requirements.txt
```

### 4. Add a CSV containing crash data
Place this CSV in the [data/](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/tree/production/data) directory.
This file will be referred to as raw_crash.csv for the remainder of this document, but it can be named whatever you like as long as you write the proper name in step 4. The file must be in the following format:
```CSV
AccidentId,IntersectionId,Vehicle_Dir,Distance,FatalInjuries,MajorInjuries,ModerateInjuries,MinorInjuries,AccidentDateTime
558201,32889,East Of,211,0,0,0,0,2016-03-13 12:09
...
```
The following format must be maintained:
* "AccidentId" is some primary key
* "Distance" is in feet. 
* "Vehicle_Dir" must be one of the following strings:
```
'At'
'North Of'
'South Of'
'East Of'
'West Of'
```
* "AccidentDateTime" must be in one of the following formats where '-' or '/' can be used as delimeters:
```
%Y-%m-%d %H:%M:%S
%Y-%m-%d %H:%M
%Y-%m-%d
```

### Run [run_all_scripts.sh](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/run_all_scripts.sh)
This will only work on Mac or Linux machines. Windows machines must follows additional steps 5-6.

### 5. Add relevant data to [.personal_data](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/.personal_data)
You must fill in the information in [.personal_data](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/.personal_data). This can be easily done with the setup script [load_personal.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/load_personal.py). The end result should look as follows:
```JSON
{
    "postgres_username": "your postgres username",
    "postgres_password": "your postgres password",
    "postgres_database_name": "your postgres database name",
    "raw_crash_csv": "the name of the CSV from last step"
}
```

### 6. Run relevant scripts
All script outputs will be kept in the [\data](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/tree/production/data) folder. If a script requires files these must be kept in the same folder.
To create all outputs run the following python scripts in this order:
1. [load_personal.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/load_personal.py)
2. [crash_location.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/crash_location.py)
3. [analytics.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/analytics.py)
4. [connected_road_data.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/connected_road_data.py)
5. [upload_roads.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/upload_roads.py)

#### [crash_location.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/crash_location.py)
This will produce output files containing the GPS coordinates of all crashes.

##### Required inputs:
* raw_crash.csv

##### Outputs:
* crash_locations.json
    * Or each crash will include actual coordinates, intersection relative location and direction, ksi, injured
* crash_locations.csv
    * The longitude and lattitude for each crash
* injured.csv
    * The longitude and lattitude of each injury
* ksi.csv
    * The longitude and lattitude of each injury

#### [analytics.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/analytics.py)
This will produce multiple files to represent data about crashes on each street segment.

##### Required inputs:
* raw_crash.csv

##### Outputs:
* street_data.json
    * For each street segment gives all statistics and crashes
* street_to_crash.csv
    * CSV file for matching street segments to crashes
* street_data.csv
    * Basic stats for each street segment

#### [connected_road_data.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/connected_road_data.py)
This will create multiple files to represent data about crashes on each road. It must be run after analytics.py.

##### Required inputs:
* street_data.json ([analytics.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/analytics.py)):

##### Outputs:
* roads.json
    * For each road will include street segment and intersections within and stats
* roads.csv
    * For each road will include geometry and stats
    * The "Geom" column is a Postgres geometry of type MultiLineString

#### [upload_roads.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/upload_roads.py)
This script imports roads.csv into postgres.

##### Required inputs:
* roads.csv ([connected_road_data.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/connected_road_data.py))