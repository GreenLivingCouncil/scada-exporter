#!/usr/bin/python
import json
import urllib2
import datetime
import re
import os
from requests import session

# URLS
SCADA_URL = "http://scadaweb.stanford.edu/ion/data/getRTxmlData.asp?dgm=//scadaweb/ion-ent/config/diagrams/ud/temp/amrit.dgm&node=WebReachDefaultDiagramNode"
DASHBOARD_LOGIN_URL = "http://buildingdashboard.net/login"
FORM_URL = "http://buildingdashboard.net/facilities/point/{form_id}/data"

# Lucid Building Dashboard login info
LUCID_USERNAME = "sashab@stanford.edu"
LUCID_PASSWORD = "stanfordglcccn"

# Data file paths
LAST_DATA_PATH = "last.json"
NEW_DATA_PATH = "current.json"
CODES_PATH = "codes.json"

# Datetime Format
DT_FORMAT = "%m/%d/%Y %H:%M:%S"

# Building entry summing specifications (see pull_data())
SUM_DEFS = [
    ("CROTHERS.STERN", ("CROTHERS.STERN_BURBANK_ZAPATA_E1152", "CROTHERS.STERN_DONNER_SERRA_E1151", "CROTHERS.STERN_TWAINS_LARKINS_E1154"))
    ]

def get_csrf_token(page_text):
    """Extract csrf token from the page content."""
    search_start = page_text.find('csrfmiddlewaretoken')
    search_end = page_text.find('>', search_start)
    match = re.search(r"value='(\w*)'", page_text[search_start:search_end])
    if not match:
        raise Exception("csrf token could not be found.")
    return match.group(1)

def smart_post(conn, url, data):
    """POST data to given url along with csrf token extracted from the same page."""
    response = conn.get(url)
    data['csrfmiddlewaretoken'] = get_csrf_token(response.text)
    return conn.post(url, data=data)

def get_form_url(building_codes):
    """Get form URL for the given set of building codes."""
    return FORM_URL.format(form_id=building_codes[1])

def rounded_hour(dt):
    """Returns the rounded hour of the given Datetime object."""
    return dt.hour if dt.minute < 30 else dt.hour + 1

def get_time_interval(last_datestring, new_datestring):
    """Build dict that defines the time interval for the given datestring range."""
    last_date = datetime.datetime.strptime(last_datestring, DT_FORMAT)
    new_date = datetime.datetime.strptime(new_datestring, DT_FORMAT)
    return {
        'localStart' :     last_date.strftime("%m/%d/%Y"),
        'localStartTime' : rounded_hour(last_date),
        'localEnd' :       new_date.strftime("%m/%d/%Y"),
        'localEndTime' :   rounded_hour(new_date)
        }

def get_submission_error(page_text):
    # TODO make this more robust?
    start = page_text.find('errorlist') + 15
    if start == 14:
        start = page_text.find('class="error"') + 14
        end = page_text.rfind('div') - 3
    else:
        end = page_text.find('</li>', start)
    return page_text[start:end]

def push_data(last_data, new_data):
    """Push data to Lucid."""
    time_interval = get_time_interval(last_data['date'], new_data['date'])
    codes = open_data(CODES_PATH)

    with session() as conn:
        # Login
        request = smart_post(conn, DASHBOARD_LOGIN_URL, {
            'username': LUCID_USERNAME,
            'password': LUCID_PASSWORD
            })

        # Upload data
        for (building_name, new_reading) in new_data['data'].items():
            # Skip if the meter for this building had an error at last reading 
            # Or if a building code doesn't exist for this building.
            if building_name not in last_data['data'] or not codes[building_name]:
                continue
            last_reading = last_data['data'][building_name]
            submit_one(conn, codes[building_name], new_reading - last_reading, time_interval)

def submit_one(conn, building_codes, value, time_interval):
    """Submit new reading for one building."""
    payload = {'value' : value}
    payload.update(time_interval)
    request = smart_post(conn, get_form_url(building_codes), payload)

    if u"Reading added" not in request.text:
        with open("dump.html", "w") as f:
            f.write(request.text.encode('ascii', 'ignore'))
        raise Exception("%s %s" % (repr(building_codes), get_submission_error(request.text)))

class BuildingNode(object):
    """Simple class to extract building info from XML node."""
    def __init__(self, xml_node):
        self.name = xml_node.attrib['nodeName']
        self.has_error = ('e' in xml_node[1].attrib)
        # strips kWh reading of any non-numeric characters, including '.' !!
        self.kwh = int(re.sub(r'[^\d]+', '', xml_node[1].attrib['v'])) 

def pull_data():
    """Pull data from SCADA XML data sheet into dict with timestamp."""
    import xml.etree.ElementTree as ET

    # Parse data from SCADA page
    response = urllib2.urlopen(SCADA_URL)
    root = ET.fromstring(response.read())
    buildings = [BuildingNode(node) for node in root]
    data = dict((building.name, building.kwh) for building in buildings
                if not (building.name == "VIP.SCADAWEB" and building.has_error))

    # Carry out definitions for combined dorms.
    for combined, parts in SUM_DEFS:
        data[combined] = sum(data[part] for part in parts)

    # Add data dict to the result
    result = {
        "date": datetime.datetime.now().strftime(DT_FORMAT),
        "data": data
        }
    return result

def save_data(data_dict, dest):
    """Thin wrapper function for dumping contents of a dict into a JSON file on disk."""
    with open(dest, 'w') as dest_f:
        json.dump(data_dict, dest_f, indent=4, sort_keys=True)

def open_data(src):
    """Thin wrapper function for returning a dict containing the contents of a JSON on disk."""
    with open(src) as src_f:
        return json.load(src_f)

def setup(overwrite=False):
    """If a last data file doesn't exist, create it from new data."""
    if not overwrite and os.path.exists(LAST_DATA_PATH):
        return
    first_data = pull_data()
    save_data(first_data, LAST_DATA_PATH)
