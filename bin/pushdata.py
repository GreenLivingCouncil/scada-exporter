#!/usr/bin/python
import cgi
import cgitb
cgitb.enable()
from string import Template
from ccn import *

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

# Emit xml message
header = "Content-Type:text/xml\n"
print header
print 
wrapper = Template("""
<transmission success="$success">
$error
</transmission>
""")
print wrapper.substitute(success=success, error=error)
