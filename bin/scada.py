"""Fetching and parsing data from the SCADA meters."""
import xml.etree.ElementTree as ET
import time
import urllib2
import re
from models import DataSet, Building
import logging
import datetime

BUILDING_BLACKLIST = ["VIP.SCADAWEB"]
SCADA_SHEET_URL = "http://scadaweb.stanford.edu/ion/data/getRTxmlData.asp?dgm=//scadaweb/ion-ent/config/diagrams/ud/temp/amrit.dgm&node=WebReachDefaultDiagramNode"
DT_FORMAT = "%Y-%m-%d %H:%M:%S"

def fetch(timeout=100):
    """Fetch and parse data from SCADA XML data sheet."""

    # Parse data from SCADA page
    sleep_time = 1
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        response = urllib2.urlopen(SCADA_SHEET_URL)
        root = ET.fromstring(response.read())
        timestamp = datetime.datetime.strptime(root.attrib['savedAt'], DT_FORMAT)
        buildings = dict((building.name, building)
                for building in map(parse_node, root)
                if building.name not in BUILDING_BLACKLIST)

        if buildings:
            break

        time.sleep(sleep_time)
        sleep_time *= 2
    else:
        raise Exception("Data fetch timed out: SCADA sheet empty.")

    now = datetime.datetime.now()
    if timestamp > datetime.datetime.now():
        logging.warning("SCADA timestamp %s is in the future (now: %s)." %
                (datetime.datetime.strftime(timestamp, DT_FORMAT),
                datetime.datetime.strftime(now, DT_FORMAT)))

    logging.debug("Data retrieved in %s seconds" % (time.time() - start_time))
    return DataSet(buildings, timestamp)

def parse_node(xml_node):
    name = xml_node.attrib['nodeName']
    kw_node = xml_node[0]
    kwh_node = xml_node[1]

    if 'e' in kwh_node.attrib:
        return Building(name, error=kwh_node.attrib['e'])
    else:
        kwh = float(kwh_node.attrib['rv'] or 0)
        kw = float(kw_node.attrib['rv'] or 0)
        return Building(name, kwh=kwh, kw=kw)


