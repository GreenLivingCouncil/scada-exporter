#!/usr/bin/python
import cgi
import cgitb
from ccn import *
import json

cgitb.enable()

form = cgi.FieldStorage()
do_reset = (form.getfirst("reset") == "true")
setup(overwrite=do_reset)

# Load data
new_data = pull_data()
save_data(new_data, "current.json")
last_data = open_data("last.json")

readings = {}
for (buildingName, dataValue) in new_data['data'].items():
    # Skip if the meter for this building had an error at last reading 
    if buildingName not in last_data['data']:
        continue

    # Build output json
    readings[buildingName] = {
            "last_reading": last_data['data'][buildingName],
            "new_reading": dataValue,
            "difference": dataValue - last_data['data'][buildingName]
            }

output = {
        "current_date": new_data['date'],
        "last_push_date": last_data['date'],
        "readings": readings
        }

print "Content-Type:application/json"
print
print json.dumps(output)
