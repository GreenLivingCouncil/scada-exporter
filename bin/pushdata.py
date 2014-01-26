#!/usr/bin/python
import cgi
import cgitb
from ccn import *
import json

cgitb.enable()

try:
    # Get data from files
    last_data = open_data(LAST_DATA_PATH)
    new_data = open_data(NEW_DATA_PATH)

    # Upload to Lucid!
    push_data(last_data, new_data)

    # Save new data as the last data
    save_data(new_data, LAST_DATA_PATH)

    # Set success flags
    success = True
    error = ""

except Exception as e:
    success = False
    error = ", ".join([unicode(elem) for elem in e.args])

print "Content-Type:application/json"
print 
print json.dumps({
        "success": success,
        "error": error
        })

