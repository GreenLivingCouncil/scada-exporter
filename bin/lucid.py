"""Convenience methods for uploading data to Building Dashboard."""
import os
import re
import logging
import requests # Requests v1.1.0
from bs4 import BeautifulSoup # BeautifulSoup v4.3.2
from models import Building, DataSet
import datetime

DATA_FORM = "https://buildingos.com/meters/{meter_id}/data/add"
DASHBOARD_LOGIN = "https://buildingos.com/login"

logging.getLogger("requests").setLevel(logging.WARNING)

class WebException(Exception):
    def __init__(self, message, request):
        Exception.__init__(self, message)

        with open("dump.html", "w") as f:
            f.write(request.text.encode('ascii', 'ignore'))

def get_csrf_token(request):
    """Extract csrf token from the page content."""
    soup = BeautifulSoup(request.text)
    csrf_tag = soup.find('input', attrs={'name': 'csrfmiddlewaretoken'})
    if not csrf_tag:
        raise WebException("csrf tag could not be found on %s" % request.url, request)

    return csrf_tag['value']

def smart_post(conn, url, data):
    """POST data to given url along with csrf token extracted from the same page."""
    request = conn.get(url, verify=False)
    data['csrfmiddlewaretoken'] = get_csrf_token(request)
    logging.debug('csrf=' + data['csrfmiddlewaretoken'])
    post_request = conn.post(url, data=data, headers={'referer': url}, verify=False)
    if post_request.status_code == 302:
        raise WebException("Login failed")
    return post_request

def get_form_url(building_code):
    """Get form URL for the given set of building codes."""
    return DATA_FORM.format(meter_id=building_code)

def rounded_hour(dt):
    """Returns the rounded hour of the given Datetime object."""
    return dt.hour if dt.minute < 30 else dt.hour + 1

def get_time_interval(last_date, new_date, totalizer=True):
    """Build dict that defines the time interval for the given datestring range."""
    if totalizer:
        return {
            'localEnd' :       new_date.strftime("%m/%d/%Y"),
            'localEndTime' :   rounded_hour(new_date)
            }
    else:
        return {
            'localStart' :     last_date.strftime("%m/%d/%Y"),
            'localStartTime' : rounded_hour(last_date),
            'localEnd' :       new_date.strftime("%m/%d/%Y"),
            'localEndTime' :   rounded_hour(new_date)
            }

def get_submission_error(request):
    soup = BeautifulSoup(request.text)
    error_list = soup.find('ul', attrs={'class': 'errorlist'})
    if not error_list:
        return None

    errors = [error_tag.string for error_tag in error_list.children]
    if len(errors) == 1:
        return errors[0]
    else:
        return str(errors)

def submit_one(conn, building_code, value, time_interval):
    """Submit new reading for one building."""
    payload = {'value' : value}
    payload.update(time_interval)
    request = smart_post(conn, get_form_url(building_code), payload)
    error = get_submission_error(request)
    if error:
        raise WebException("Error submitting %s: %s" % (building_code, error), request)

def submit(last_data, new_data, codes, username, password, totalizer=True):
    """Push data to Lucid."""

    with requests.session() as conn:
        # Login
        request = smart_post(conn, DASHBOARD_LOGIN, {
                'username': username,
                'password': password
            })

        # Upload data
        for (building_name, new_reading) in new_data.buildings.items():
            last_reading = last_data.buildings[building_name]

            # Skip if building codes don't exist for this building, or if problems with meter.
            if building_name not in codes or not codes[building_name]:
                logging.debug("Skipping %s, no code exists" % building_name)
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
            time_interval = get_time_interval(last_data.date, new_data.date, totalizer)
            if totalizer:
                value = new_reading.kwh
            else:
                value = new_reading.kwh - last_reading.kwh

            submit_one(conn, codes[building_name], value, time_interval)
            logging.debug("Submitted %s kWh for %s" % (value, building_name))


