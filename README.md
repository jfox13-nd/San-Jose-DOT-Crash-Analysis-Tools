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
* "IntersectionId" is a key used internally by the DOT to refer to intersections uniquely
    * "IntersectionId" corresponds to the column "intnum" in the "intersections" table
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
Your machine must be able to run Bash scripts to execute this script (if you are using a Mac or Linux machine then you should be able to run this script). If your machine cannot run Bash scripts then you must follow steps 5-6.

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
    * For each crash will include actual coordinates, intersection relative location and direction, KSI, injured
* crash_locations.csv
    * The longitude and latitude for each crash
* injured.csv
    * The longitude and latitude of each injury
* ksi.csv
    * The longitude and latitude of each injury

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

## Modifying This Repository For Other Cities
This repository could not be immediately used with data from another city, however it could be modified to support another city if that city's crash data is structured in a similar way. This would also neccesitate the modification of the repository [San-Jose-DOT-Crash-Locator](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator) which this repository is dependent upon.

The following points must be largely consistent between San Jose and the new city if this repository can be modified to find and analyze crashes in that new city:
1. The city base map must be structured similarly
    * The base map of the city must include point intersections and line street segments
    * Street segment lines start and end at intersections and given a street segment one can quickly retrieve the IDs of these intersections
    * A street segment is not bisected by any intersections or other street segments.
        * Street segments only meet at intersections and a street segment only touches intersections at the start or end of a line
    * There are no overlapping intersections
2. Certain data must be collected for each collision
    * Some unique ID for that collision
    * The intersection closest to the the crash
        * Preferably there is some intersection ID available for each intersection
        * If only the names of the intersecting streets are available consider implementing a fuzzy matching algorithim to find the intersection ID
    * The cardinal direction from the intersection to the collision
    * The distance between the intersection and the collision

Here are some of the steps required to modify this repository if the previously mentioned points are consistent:
1. Update the `findcrashlocation()` SQL Funtion from the repository [San-Jose-DOT-Crash-Locator](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator).
    * Information on how to update that function is available at the bottom of its [README.md](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator/blob/master/README.md)
2. Update any SQL in the scripts [crash_location.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/crash_location.py), [analytics.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/analytics.py), and [connected_road_data.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/connected_road_data.py)
    * Rewrite any SQL code to logically replace attributes related to San Jose with attributes related to the new city
3. Update references to KSI and injuries in the scripts [crash_location.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/crash_location.py), [analytics.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/analytics.py), [connected_road_data.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/connected_road_data.py), and [utils.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/utils.py) to reflect whatever measurements your city collects on crashes
4. Update [utils.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/utils.py) and [load_personal.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/load_personal.py) to reflect any changes you might need to make to the input CSV format (raw_crash.csv).


If you are trying to modify this repository for a new city feel free to ask me questions:
Email: jfox13@nd.edu