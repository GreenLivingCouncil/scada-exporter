"""Fetching and parsing data from the SCADA meters."""
import xml.etree.ElementTree as ET
import time
import urllib2
import re
from models import DataSet, BuildingNode

BUILDING_BLACKLIST = set(["VIP.SCADAWEB"])

# Building entry summing specifications
SUM_DEFS = [
    ("CROTHERS.STERN", ("CROTHERS.STERN_BURBANK_ZAPATA_E1152", "CROTHERS.STERN_DONNER_SERRA_E1151", "CROTHERS.STERN_TWAINS_LARKINS_E1154"))
    ]

def fetch(data_url, timeout=100):
    """Fetch and parse data from SCADA XML data sheet."""

    # Parse data from SCADA page
    sleep_time = 1
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        response = urllib2.urlopen(data_url)
        root = ET.fromstring(response.read())
        buildings_raw = [get_building_node(node) for node in root]
        buildings = dict((building.name, building)
                for building in buildings_raw
                if building not in BUILDING_BLACKLIST)

        if buildings:
            break

        time.sleep(sleep_time)
        sleep_time *= 2
    else:
        raise Exception("Data fetch timed out: SCADA sheet empty.")

    # FIXME make global logger
    # logging.debug("Data retrieved in %s seconds" % time.time() - start_time)

    # Carry out definitions for combined dorms.
    for combined, parts in SUM_DEFS:
        buildings[combined] = BuildingNode.combine(combined, [buildings[part] for part in parts])

    return DataSet(buildings)

def get_building_node(xml_node):
    name = xml_node.attrib['nodeName']
    kw_node = xml_node[0]
    kwh_node = xml_node[1]

    if 'e' in kwh_node.attrib:
        return BuildingNode(name, error=kwh_node.attrib['e'])
    else:
        # strips kWh reading of any non-numeric characters, including '.' !!
        kwh = float(re.sub(r'[^\d\.]', '', kwh_node.attrib['v']) or 0)
        kw = float(re.sub(r'[^\d\.]', '', kw_node.attrib['v']) or 0)
        return BuildingNode(name, kwh=kwh, kw=kw)


