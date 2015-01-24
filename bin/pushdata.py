#!/usr/bin/python
import cgi
import cgitb
import json
import ccn
import logging
from lucid import WebException

cgitb.enable()

try:
    # Upload to Lucid!
    ccn.push_data()

    # Set success flags
    success = True
    error = None

except WebException as e:
    logging.error(e)
    success = False
    error = e.message

print "Content-Type:application/json"
print 
print json.dumps({
        "success": success,
        "error": error
        })

