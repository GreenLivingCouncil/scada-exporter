#!/usr/bin/python
import cgi
import cgitb
cgitb.enable()
from string import Template
from ccn import *

form = cgi.FieldStorage()
setup(overwrite=(form.getfirst("reset") == "true"))
# Get newest data and save it to the temp file
new_data = pull_data()
save_data(new_data, "current.json")
# Open last data
last_data = open_data("last.json")
buildingTags = []
for (buildingName, dataValue) in new_data['data'].items():
    # Skip if the meter for this building had an error at last reading 
    if buildingName not in last_data['data']:
        continue
    dataTags = [
        wrap_data(last_data['data'][buildingName]),
        wrap_data(dataValue),
        wrap_data(dataValue - last_data['data'][buildingName])
    ]
    buildingTags.append('<building name="%s">%s</building>'% (buildingName, '\n'.join(dataTags)))

header = "Content-Type:text/xml\n"

print header
print
wrapper = Template("""
<transmission>
    <date value="$date" />
    $data
</transmission>
""")
print wrapper.substitute(date=last_data['date'], data='\n'.join(buildingTags))
