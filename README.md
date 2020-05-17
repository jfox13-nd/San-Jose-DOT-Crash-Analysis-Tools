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

### 2. Clone and setup the [San-Jose-DOT-Crash-Locator Repo](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator)
Make sure to follow all setup instructions and confirm that your postgres database is running before proceeding.
You do not clone the [San-Jose-DOT-Crash-Locator Repo](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator) into this repository.
```bash
git clone https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator.git
```

### 3. Add a CSV containing crash data
Place this CSV in the [data/](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/tree/production/data) directory.
This file will be referred to as raw_crash.csv for the remainder of this document, but it can be named whatever you like as long as you write the proper name in step 4. The file must be in the following format:
```CSV
AccidentId,IntersectionId,Vehicle_Dir,Distance,FatalInjuries,MajorInjuries,ModerateInjuries,MinorInjuries,AccidentDateTime
558201,32889,East Of,211,0,0,0,0,2016-03-13 12:09
...
```
Where "AccidentId" is some primary key.

### 4. Add relevant data to [.personal_data](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/.personal_data)
You must fill in the information in [.personal_data](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/.personal_data). This can be easily done with the setup script [load_personal.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/load_personal.py). The end result should look as follows:
```JSON
{
    "postgres_username": "your postgres username",
    "postgres_database_name": "your postgres database name",
    "raw_crash_csv": "the name of the CSV from last step"
}
```

### 5. Run relevant scripts
All script outputs will be kept in the [\data](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/tree/production/data) folder. If a script requires files these must be kept in the same folder.
Running the bash script [run_all_scripts.sh](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/run_all_scripts.sh) will run all scripts in the correct order, including [load_personal.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/load_personal.py).

#### [crash_location.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/crash_location.py)
This will produce output files containing the GPS coordinates of all crashes.

##### Required inputs:
raw_crash.csv

##### Outputs:
crash_locations.json: for each crash will include actual coordinates, intersection relative location and direction, ksi, injured
crash_locations.csv: the longitude and lattitude for each crash
injured.csv: the longitude and lattitude of each injury
ksi.csv: the longitude and lattitude of each injury

#### [analytics.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/analytics.py)
This will produce multiple files to represent data about crashes on each street segment.

##### Required inputs:
raw_crash.csv

##### Outputs:
street_data.json: for each street segment gives all statistics and crashes
street_to_crash.csv: csv file for matching street segments to crashes
street_data.csv: basic stats for each street segment

#### [connected_road_data.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/connected_road_data.py)
This will create multiple files to represent data about crashes on each road. It must be run after analytics.py.

##### Required inputs:
street_data.json ([analytics.py](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Analysis-Tools/blob/production/analytics.py)):

##### Outputs:
roads.json: for each road will include street segment and intersections within and stats
roads.csv: for each road will include geometry and stats
