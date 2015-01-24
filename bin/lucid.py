"""Convenience methods for uploading data to Building Dashboard."""
import os
from requests import session
from models import Building, DataSet

DATA_FORM = "http://buildingdashboard.net/facilities/point/{meter_id}/data"
DASHBOARD_LOGIN = "http://buildingdashboard.net/login"

# FIXME replace naive searching with HTML parser

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

def get_time_interval(last_date, new_date):
    """Build dict that defines the time interval for the given datestring range."""
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

    if "Reading added" not in request.text:
        raise WebException("%s %s" % (building_code, get_submission_error(request)), request)

def submit(last_data, new_data, codes, totalizer=True):
    """Push data to Lucid."""
    time_interval = get_time_interval(last_data.date, new_data.date)

    with session() as conn:
        # Login
        request = smart_post(conn,
            config.get("urls", "dashboard-login"),
            {
                'username': config.get("lucid-login", "username"),
                'password': config.get("lucid-login", "password")
            })

        # Upload data
        for (building_name, new_reading) in new_data.buildings.items():
            last_reading = last_data.buildings[building_name]

            # Skip if building codes don't exist for this building, or if problems with meter.
            if not codes[building_name]:
                logging.warning("Skipping %s, no code exists" % building_name)
                continue

            # Skip if there are interfering meter errors
            if new_reading.error:
                logging.warning("Skipping %s, error on new reading: %s" % (building_name, new_reading.error))
                continue
            if not totalizer and last_reading.error:
                logging.warning("Skipping %s, error on last reading: %s" % (building_name, last_reading.error))
                continue

            # Building Dashboard used to ask for the kWh's used over the specified time interval,
            # but is now compatible with the totalizer data
            if totalizer:
                value = new_reading.kwh
            else:
                value = new_reading.kwh - last_reading.kwh

            submit_one(conn, codes[building_name], value, time_interval)
            logging.info("Submitted %s kWh for %s" % (value, building_name))


