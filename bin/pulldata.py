#!/usr/bin/python
import cgi
import cgitb
from ccn import *
import json

cgitb.enable()

form = cgi.FieldStorage()
do_reset = (form.getfirst("reset") == "true")
setup(overwrite=do_reset)

# Load and update data
new_data = pull_data()
save_data(new_data, "current.json")
last_data = open_data("last.json")

# Build output json
readings = dict(
    (building_name, {"last_reading": last_reading, "new_reading": new_reading, "difference": difference})
    for (building_name, last_reading, new_reading, difference)
    in iter_readings(last_data, new_data)
    )
output = {
        "current_date": new_data['date'],
        "last_push_date": last_data['date'],
        "readings": readings
        }

print "Content-Type:application/json"
print
print json.dumps(output)
