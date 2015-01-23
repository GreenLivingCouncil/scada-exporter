"""Convenience methods for uploading data to Building Dashboard."""
import os
from requests import session
from models import BuildingNode, DataSet

DATA_FORM = "http://buildingdashboard.net/facilities/point/{meter_id}/data"
DASHBOARD_LOGIN = "http://buildingdashboard.net/login"

# FIXME replace naive searching with HTML parser

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
    return DATA_FORM.format(meter_id=building_code)

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

def submit_one(conn, building_code, value, time_interval):
    """Submit new reading for one building."""
    payload = {'value' : value}
    payload.update(time_interval)
    request = smart_post(conn, get_form_url(building_code), payload)

    if u"Reading added" not in request.text:
        raise WebException("%s %s" % (building_code, get_submission_error(request)), request)

def push_data(last_data, new_data, config, totalizer=True):
    """Push data to Lucid."""
    time_interval = get_time_interval(last_data['date'], new_data['date'])
    codes = open_data(config.get("file-paths", "codes"))

    with session() as conn:
        # Login
        request = smart_post(conn,
            config.get("urls", "dashboard-login"),
            {
                'username': config.get("lucid-login", "username"),
                'password': config.get("lucid-login", "password")
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


