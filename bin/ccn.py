import json
import datetime
import re
import os
import logging
import ConfigParser
import lucid

logging.basicConfig(filename="ccn.log", level=logging.DEBUG, format='[%(asctime)s] %(message)s')

config = ConfigParser.ConfigParser()
config.read("config.ini")

# Datetime Format
DT_FORMAT = "%m/%d/%Y %H:%M:%S"

def setup(overwrite=False):
    """If a last data file doesn't exist, create it from new data."""
    last_data_path = config.get("file-paths", "last-data")
    if not overwrite and os.path.exists(last_data_path):
        return
    first_data = pull_data()
    save_data(first_data, last_data_path)
    logging.warning("Overwrote or created new %s" % last_data_path)
