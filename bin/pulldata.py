#!/usr/bin/python
import cgi
import cgitb
import json
import ccn

cgitb.enable()

form = cgi.FieldStorage()
if form.getfirst("reset") == "true":
    ccn.reset_data()

# Load and update data
ccn.update_data()

# Build output json
def iter_readings():
    for (name, new_reading) in ccn.new_data.buildings.items():
        last_reading = ccn.last_data.buildings[name]

        errors = []
        if last_reading.error:
            errors += ["Last reading: %s" % last_reading.error]
        if new_reading.error:
            errors += ["New reading: %s" % last_reading.error]

        entry = {
            "error": '<br/>'.join(errors),
            "last_reading": last_reading.kwh,
            "new_reading": new_reading.kwh,
            "difference": new_reading.kwh - last_reading.kwh
            }
        yield (name, entry)

output = {
        "current_date": str(ccn.new_data.date),
        "last_push_date": str(ccn.last_data.date),
        "readings": dict(iter_readings())
        }

print "Content-Type:application/json"
print
print json.dumps(output)
