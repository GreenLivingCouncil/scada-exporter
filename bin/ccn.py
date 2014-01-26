#!/usr/bin/python
import json
import urllib2
import datetime
import os
from requests import session

SCADA_URL = "http://scadaweb.stanford.edu/ion/data/getRTxmlData.asp?dgm=//scadaweb/ion-ent/config/diagrams/ud/temp/amrit.dgm&node=WebReachDefaultDiagramNode"
DASHBOARD_LOGIN_URL = "http://buildingdashboard.net/login"
LAST_DATA_PATH = "last.json"
NEW_DATA_PATH = "current.json"
DT_FORMAT = "%m/%d/%Y %H:%M:%S"

def get_csrf_token(page_text):
    token_i = page_text.find('csrfmiddlewaretoken') + 28
    token_end = page_text.find('\'', token_i)
    return page_text[token_i:token_end]

def smart_post(conn, url, data):
    response = conn.get(url)
    data['csrfmiddlewaretoken'] = get_csrf_token(response.text)
    return conn.post(url, data=data)

def get_form_url(building_codes):
    return ("http://buildingdashboard.net/facilities/point/%s/data" % building_codes[1])

def rounded_hour(dt):
    """Returns the rounded hour of the given Datetime object."""
    return dt.hour if dt.minute < 30 else dt.hour + 1

def get_time_interval(last_datestring, new_datestring):
    last_date = datetime.datetime.strptime(last_datestring, DT_FORMAT)
    new_date = datetime.datetime.strptime(new_datestring, DT_FORMAT)
    return (
        last_date.strftime("%m/%d/%Y"),
        rounded_hour(last_date),
        new_date.strftime("%m/%d/%Y"),
        rounded_hour(new_date)
        )

def get_submission_error(page_text):
    start = page_text.find('errorlist') + 15
    if start == 14:
        start = page_text.find('class="error"') + 14
        end = page_text.rfind('div') - 3
    else:
        end = page_text.find('</li>', start)
    return page_text[start:end]

def push_data(last_data, new_data):
    # Get the needed values from the datestrings
    time_interval = get_time_interval(last_data['date'], new_data['date'])

    # Open the dictionary for building codes
    with open('codes.json') as codes_f:
        codes = json.load(codes_f)

    with session() as c:
        # Login
        payload = {
            'username': 'sashab@stanford.edu',
            'password': 'stanfordglcccn'
            }
        request = smart_post(c, DASHBOARD_LOGIN_URL, data=payload)

        # Upload data
        for (buildingName, dataValue) in new_data['data'].items():
            # Skip if the meter for this building had an error at last reading 
            if buildingName not in last_data['data']:
                continue
            submit_one(c, codes[buildingName], dataValue - last_data['data'][buildingName], time_interval)

def submit_one(conn, building_codes, data_val, time_interval):
    if not building_codes:
        return

    payload = {
        'localStart': time_interval[0],
        'localStartTime': time_interval[1],
        'localEnd': time_interval[2],
        'localEndTime': time_interval[3],
        'value': data_val
        }
    request = smart_post(conn, get_form_url(building_codes), payload)
    if u"Reading added" not in request.text:
        with open("dump.html", "w") as f:
            f.write(request.text.encode('ascii', 'ignore'))
        raise Exception("%s %s" % (repr(building_codes), get_submission_error(request.text)))

def pull_data():
    import xml.etree.ElementTree as ET

    # Get date and create result dict
    datestring = datetime.datetime.now().strftime(DT_FORMAT)

    # Get data from SCADA page
    response = urllib2.urlopen(SCADA_URL)
    root = ET.fromstring(response.read())
    # Loop through building nodes and add data to a new dict
    data = {}
    for buildingNode in root:
        buildingName = buildingNode.attrib['nodeName']
        if buildingName == "VIP.SCADAWEB":
            continue
        # Skip if there's an error message attribute
        if "e" in buildingNode[1].attrib:
            continue
        # Sum up the Stern dorms
        if buildingName in ["CROTHERS.STERN_BURBANK_ZAPATA_E1152", "CROTHERS.STERN_DONNER_SERRA_E1151", "CROTHERS.STERN_TWAINS_LARKINS_E1154"]:
            if "CROTHERS.STERN" not in data:
                data["CROTHERS.STERN"] = 0
            data["CROTHERS.STERN"] += int(buildingNode[1].attrib['v'].translate(None, ', '))
        # Put in data
        data[buildingName] = int(buildingNode[1].attrib['v'].translate(None, ', '))

    # Add data dict to the result
    result = {
        "date": datestring,
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
        result = json.load(src_f)
    return result

def setup(overwrite=False):
    """If a last data file doesn't exist, create it from new data."""
    if not overwrite and os.path.exists(LAST_DATA_PATH):
        return
    first_data = pull_data()
    save_data(first_data, LAST_DATA_PATH)
