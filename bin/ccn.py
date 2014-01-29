#!/usr/bin/python
import json
import urllib2
import datetime
import re
import os
from requests import session
import logging

logging.basicConfig(filename="ccn.log", level=logging.DEBUG, format='[%(asctime)s] %(message)s')

# URLS
SCADA_URL = "http://scadaweb.stanford.edu/ion/data/getRTxmlData.asp?dgm=//scadaweb/ion-ent/config/diagrams/ud/temp/amrit.dgm&node=WebReachDefaultDiagramNode"
DASHBOARD_LOGIN_URL = "http://buildingdashboard.net/login"
FORM_URL = "http://buildingdashboard.net/facilities/point/{meter_id}/data"

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

class WebException(Exception):
    def __init__(self, message, request):
        Exception.__init__(self, message)

        with open("dump.html", "w") as f:
            f.write(request.text.encode('ascii', 'ignore'))


def get_csrf_token(request):
    """Extract csrf token from the page content."""
    page_text = request.text
    search_start = page_text.find('csrfmiddlewaretoken')
    search_end = page_text.find('>', search_start)
    search_string = page_text[search_start:search_end]
    match = re.search(r"value='(\w*)'", search_string)
    if not match:
        raise WebException("csrf token could not be found in: %s" % search_string, request)
    return match.group(1)

def smart_post(conn, url, data):
    """POST data to given url along with csrf token extracted from the same page."""
    request = conn.get(url)
    data['csrfmiddlewaretoken'] = get_csrf_token(request)
    return conn.post(url, data=data)

def get_form_url(building_code):
    """Get form URL for the given set of building codes."""
    return FORM_URL.format(meter_id=building_code)

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

def get_submission_error(request):
    # TODO make this more robust?
    page_text = request.text
    start = page_text.find('errorlist') + 15
    if start == 14:
        start = page_text.find('class="error"') + 14
        end = page_text.rfind('div') - 3
    else:
        end = page_text.find('</li>', start)
    return page_text[start:end]

def iter_readings(last_data, new_data):
    for (building_name, new_reading) in new_data['data'].items():
        last_reading = last_data['data'][building_name]
            
        if type(new_reading) is not int:
            entry = {
                "error": new_reading
                }
        elif type(last_reading) is not int:
            entry = {
                "error": ("%s [fixed in new reading]" % last_reading)
                }
        else:
            entry = {
                "last_reading": last_reading,
                "new_reading": new_reading,
                "difference": new_reading - last_reading
                }
        yield (building_name, entry)

def push_data(last_data, new_data, totalizer=True):
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
        for (building_name, entry) in iter_readings(last_data, new_data):
            # Skip if building codes don't exist for this building, or if problems with meter.
            if not codes[building_name]:
                continue
            if "error" in entry:
                logging.warning("Skipped %s due to meter error: %s" % (building_name, entry['error']))
                continue
            value = entry['new_reading'] if totalizer else entry['difference']
            submit_one(conn, codes[building_name], value, time_interval)
            logging.info("Submitted %s kWh for %s" % (value, building_name))

def submit_one(conn, building_code, value, time_interval):
    """Submit new reading for one building."""
    payload = {'value' : value}
    payload.update(time_interval)
    request = smart_post(conn, get_form_url(building_code), payload)

    if u"Reading added" not in request.text:
        raise WebException("%s %s" % (building_code, get_submission_error(request)), request)

class BuildingNode(object):
    """Simple class to extract building info from XML node."""
    def __init__(self, xml_node):
        self.name = xml_node.attrib['nodeName']
        self.error = xml_node[1].attrib['e'] if 'e' in xml_node[1].attrib else ""
        # strips kWh reading of any non-numeric characters, including '.' !!
        self.kwh = int(re.sub(r'[^\d]+', '', xml_node[1].attrib['v'])) 

def pull_data():
    """Pull data from SCADA XML data sheet into dict with timestamp."""
    import xml.etree.ElementTree as ET
    import time

    # Parse data from SCADA page
    sleep_time = 1
    while True:
        response = urllib2.urlopen(SCADA_URL)
        root = ET.fromstring(response.read())
        buildings = [BuildingNode(node) for node in root]
        data = dict((building.name, building.error or building.kwh) 
                    for building in buildings
                    if not building.name == "VIP.SCADAWEB")
        if data:
            break
        elif sleep_time > 100:
            raise Exception("Data pull timed out: SCADA sheet perpetually empty.")
        else:
            time.sleep(sleep_time)
            sleep_time *= 2
    logging.debug("Data retrieved before sleep_time = %s" % sleep_time)

    # Carry out definitions for combined dorms.
    for combined, parts in SUM_DEFS:
        # skip if there is a hole in the constituent data
        if any(type(data[part]) is not int for part in parts):
            data[combined] = "Error in constituent building meter (at least one of %s)." % ", ".join(parts)
            continue
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
    logging.warning("Overwrote or created new %s" % LAST_DATA_PATH)
