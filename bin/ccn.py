import ConfigParser
import logging
import os
import json
import scada
import lucid
from models import DataSet

logging.basicConfig(filename='ccn.log', level=logging.DEBUG, format='[%(asctime)s] %(message)s')

config = ConfigParser.ConfigParser()
config.optionxform = str
config.read('config.ini')

combine_defs = dict((combination, config.get('combine-definitions', combination).split(','))
    for combination in config.options('combine-definitions'))
last_data_path = config.get('file-paths', 'last-data')
new_data_path = config.get('file-paths', 'new-data')
new_data = None
last_data = None

def push_data():
    global last_data, new_data
    """Push data to Building Dashboard and reset last data with new data."""
    with open(config.get("file-paths", "codes")) as codes_file:
        codes = json.load(codes_file)

    lucid.submit(last_data, new_data, codes,
            config.get('lucid-login', 'username'),
            config.get('lucid-login', 'password'))
    os.rename(new_data_path, last_data_path)
    last_data = new_data
    update_data()

def update_data():
    """Updates data with new measurements from SCADA meters."""
    global new_data
    new_data = scada.fetch()
    new_data.apply_combinations(combine_defs)
    new_data.save(new_data_path)

def reset_data():
    """Resets the data files with new data."""
    os.remove(last_data_path)
    logging.info("Deleted %s" % last_data_path)
    os.remove(new_data_path)
    logging.info("Deleted %s" % new_data_path)
    init_data()
    load_data()

def init_data():
    """Creates the first data file if it doesn't exist yet."""
    global new_data
    if os.path.exists(last_data_path) and os.path.exists(new_data_path):
        return

    first_data = scada.fetch()
    first_data.apply_combinations(combine_defs)

    if not os.path.exists(last_data_path):
        first_data.save(last_data_path)
        logging.info("Created %s" % last_data_path)

    if not os.path.exists(new_data_path):
        first_data.save(new_data_path)
        logging.info("Created %s" % new_data_path)

def load_data():
    global last_data, new_data
    last_data = DataSet.load(config.get('file-paths', 'last-data'))
    new_data = DataSet.load(config.get('file-paths', 'new-data'))

init_data()
load_data()
