# Crash Data Analysis tools

## Setup

### 1. Clone this repository
```bash
git clone PUT URL HERE
```

### 2. Clone and setup the [San-Jose-DOT-Crash-Locator Repo](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator)
Make sure to follow all setup instructions and confirm that your postgres database is running before proceeding.
You do not clone the [San-Jose-DOT-Crash-Locator Repo](https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator) into this repository.
```bash
git clone https://github.com/jfox13-nd/San-Jose-DOT-Crash-Locator.git
```

### 3. Add a CSV containing crash data in the following format:
Place this csv in the data/ directory.
This document will be referred to as raw_crash.csv for the remainder of this document, but it can be named whatever you like as long as you write the proper name in step 4.
```CSV
AccidentId,DateDimId,AccidentDateTime,TcrNumber,IntersectionDimId,IntersectionId,Latitude,Longitude,Vehicle_Dir,Distance,AStreetPrefixDirection,AStreetNameAndSuffix,AStreetSuffixDirection,AStreetType,BStreetPrefixDirection,BStreetNameAndSuffix,BStreetSuffixDirection,BStreetType,MapPage,MapQuadrant,CouncilDistrict,Jurisdiction,TrafficControlType,ATIntersection,BTIntersection,A1WayIntersection,B1WayIntersection,Shop,IntersectionDirection,IntersectionType,SniDistrict,Int_Type,Vehicle_Involved_With,Road_Cond,Light_Cond,Weather,Road_Surface,Collision_Type,Prim_Collision_Factor,Ped_Dir,Ped_Action,Traffic_Control,CityDamageFlag,ShortFormFlag,FatalInjuries,MajorInjuries,ModerateInjuries,MinorInjuries,ESRI_OID
123456,20160313,2016-03-13 12:54,123456789,139,2408,37.33181787,-121.9047284,At,,E-W,ALAMEDA ,,AR,N-S,BUSH ST,,LO,83,10,6,San Jose,1 Way Stop,S,,,,,SOUTH,T,,Intersection,Pedestrian,No Unusual Conditions,Daylight,Rain,Wet,Vehicle/Pedestrian,Unknown,West,Crossing In Crosswalk - Not At Intersection,Controls Functioning,N,N,0,0,0,1,1
...
```

### Add relevant data to .personal_data
You must fill in the information for 
```JSON
{
    "postgres_username": "your postgres username",
    "postgres_database_name": "your postgres database name",
    "raw_crash_csv": "the name of the CSV from last step"
}
```

### Run relevant scripts
All script outputs will be kept in the \data folder. If a script requires files these must be kept in the same folder.

#### crash_location.py
This will produce output files containing the GPS coordinates of all crashes.

##### Required inputs:
raw_crash.csv

##### Outputs:
crash_locations.json: for each crash will include actual coordinates, intersection relative location and direction, ksi, injured
crash_locations.csv: the longitude and lattitude for each crash
injured.csv: the longitude and lattitude of each injury
ksi.csv: the longitude and lattitude of each injury

#### analytics.py
This will produce multiple files to represent data about crashes on each street segment.

##### Required inputs:
raw_crash.csv

##### Outputs:
street_data.json: for each street segment gives all statistics and crashes
street_to_crash.csv: csv file for matching street segments to crashes
street_data.csv: basic stats for each street segment

#### connected_road_data.py
This will create multiple files to represent data about crashes on each road. It must be run after analytics.py.

##### Required inputs:
street_data.json (analytics.py):

##### Outputs:
roads.json: for each road will include street segment and intersections within and stats
roads.csv: for each road will include geometry and stats
