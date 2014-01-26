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
readings = dict(iter_readings(last_data, new_data))
output = {
        "current_date": new_data['date'],
        "last_push_date": last_data['date'],
        "readings": readings
        }

print "Content-Type:application/json"
print
print json.dumps(output)
