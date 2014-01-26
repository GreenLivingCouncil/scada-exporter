#!/usr/bin/python
import json
import xml.etree.ElementTree as ET
import urllib2
import datetime
import os
from requests import session

def get_csrf_token(page_text):
    token_i = page_text.find('csrfmiddlewaretoken') + 28
    token_end = page_text.find('\'', token_i)
    return page_text[token_i:token_end]

def get_form_url(building_id, form_id):
    return ("http://buildingdashboard.net/facilities/%s/manual/%s/save" % (building_id, form_id))

def round_time(timestring):
    if int(timestring[3:]) > 30:
        return str(int(timestring[:2]) + 1)
    return str(int(timestring[:2]))

def get_time_interval(last_datestring, new_datestring):
    return (last_datestring[:10], round_time(last_datestring[11:16]), new_datestring[:10], round_time(new_datestring[11:16]))

def push_data(last_data, new_data):
    # Get the needed values from the datestrings
    time_interval = get_time_interval(last_data['date'], new_data['date'])
    # Open the dictionary for building codes
    with open('codes.json') as codes_f:
        codes= json.load(codes_f)
    with session() as c:
        # Login
        request = c.get('http://buildingdashboard.net/login/?next=/')
        payload = {
            'username': 'sashab@stanford.edu',
            'password': 'stanfordglcccn',
            'csrfmiddlewaretoken': get_csrf_token(request.text)
        }
        request = c.post('http://buildingdashboard.net/login/?next=/', data=payload)

        # Upload data
        for (buildingName, dataValue) in new_data['data'].items():
            # Skip if the meter for this building had an error at last reading 
            if buildingName not in last_data['data']:
                continue
            submit_one(c, codes[buildingName], dataValue - last_data['data'][buildingName], time_interval)

def submit_one(conn, building_codes, data_val, time_interval):
    if building_codes == 0:
        return
    request = conn.get(get_form_url(building_codes[0], building_codes[1]))
    payload = {
        'localStart': str(time_interval[0]),
        'localStartTime': str(time_interval[1]),
        'localEnd': str(time_interval[2]),
        'localEndTime': str(time_interval[3]),
        'value': str(data_val),
        'csrfmiddlewaretoken': str(get_csrf_token(request.text))
    }
    request = conn.post(get_form_url(building_codes[0], building_codes[1]), data=payload)
    if u"Reading added" not in request.text:
        with open("dump.html", "w") as f:
            f.write(request.text.encode('ascii', 'ignore'))
            f.write(repr(payload))
            f.flush()
        raise Exception("%s %s" % (repr(building_codes), get_submission_error(request.text)))

def get_submission_error(page_text):
    start = page_text.find('errorlist') + 15
    if start == 14:
        start = page_text.find('class="error"') + 14
        end = page_text.rfind('div') - 3
    else:
        end = page_text.find('</li>', start)
    return page_text[start:end]

def setup(overwrite=False):
    if not overwrite and os.path.exists("last.json"):
        return
    first_data = pull_data()
    save_data(first_data, "last.json")

def pull_data():
    # Get date and create result dict
    datestring = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    result = {'date': datestring}
    # Get data from SCADA page
    response = urllib2.urlopen('http://scadaweb.stanford.edu/ion/data/getRTxmlData.asp?dgm=//scadaweb/ion-ent/config/diagrams/ud/temp/amrit.dgm&node=WebReachDefaultDiagramNode')
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
        # Sum up the Stern dorms... remove this when officially split up
        if buildingName in ["CROTHERS.STERN_BURBANK_ZAPATA_E1152", "CROTHERS.STERN_DONNER_SERRA_E1151", "CROTHERS.STERN_TWAINS_LARKINS_E1154"]:
            if "CROTHERS.STERN" not in data:
                data["CROTHERS.STERN"] = 0
            data["CROTHERS.STERN"] += int(buildingNode[1].attrib['v'].translate(None, ', '))
        # Put in data
        data[buildingName] = int(buildingNode[1].attrib['v'].translate(None, ', '))

    # Add data dict to the result
    result['data'] = data
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
