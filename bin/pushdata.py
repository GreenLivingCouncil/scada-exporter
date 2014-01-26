#!/usr/bin/python
import cgi
import cgitb
cgitb.enable()
from string import Template
from ccn import *
import json

try:
    # Get data from files
    last_data = open_data("last.json")
    new_data = open_data("current.json")

    # Upload to Lucid!
    push_data(last_data, new_data)

    # Save new data as the last data
    save_data(new_data, "last.json")

    # Set success flags
    success = "true"
    error = ""
except Exception as e:
    success = "false"
    error = e.args[0]

print "Content-Type:application/json"
print 
print json.dumps({
        "success": success,
        "error": ", ".join([unicode(elem) for elem in e.args])
        })

# wrapper = Template("""
# <transmission success="$success">
# $error
# </transmission>
# """)
# print wrapper.substitute(success=success, error=error)
