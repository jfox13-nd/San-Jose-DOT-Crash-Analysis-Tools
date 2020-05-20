#!/bin/bash

run_and_check () {
    echo ""
    echo "Running $1"
    python3 $1

    if [ $? -ne 0 ]
    then
        echo "$1 failed"
        exit 1
    fi
}

for i in "load_personal.py" "crash_location.py" "analytics.py" "connected_road_data.py" "upload_roads.py";
    do
        run_and_check $i
    done

exit 0