#!/usr/bin/python
import cgi
import cgitb
from ccn import *
import json

cgitb.enable()

try:
    # Get data from files
    last_data = open_data("last.json")
    new_data = open_data("current.json")

    # Upload to Lucid!
    push_data(last_data, new_data)

    # Save new data as the last data
    save_data(new_data, "last.json")

    # Set success flags
    success = True
    error = ""
except Exception as e:
    success = False
    error = e.args[0]

print "Content-Type:application/json"
print 
print json.dumps({
        "success": success,
        "error": ", ".join([unicode(elem) for elem in e.args])
        })

