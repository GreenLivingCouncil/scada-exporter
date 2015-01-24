import ConfigParser
import logging
import os
import scada
import lucid
from models import DataSet

logging.basicConfig(filename='ccn.log', level=logging.DEBUG, format='[%(asctime)s] %(message)s')

config = ConfigParser.ConfigParser()
config.read('config.ini')

last_data_path = config.get('file-paths', 'last-data')
new_data_path = config.get('file-paths', 'new-data')

def push_data():
    """Push data to Building Dashboard and reset last data with new data."""
    with open(config.get("file-paths", "codes")) as codes_file:
        codes = json.load(codes_file)

    lucid.submit(last_data, new_data, codes)
    os.rename(new_data_path, last_data_path)
    last_data = new_data

def update_data():
    """Updates data with new measurements from SCADA meters."""
    new_data = scada.fetch(config.get('urls','scada-sheet'))
    new_data.save(new_data_path)

def reset_data():
    """Resets the data files with new data."""
    os.remove(last_data_path)
    logging.info("Deleted %s" % last_data_path)
    os.remove(new_data_path)
    logging.info("Deleted %s" % new_data_path)
    init_data()

def init_data():
    """Creates the first data file if it doesn't exist yet."""
    if os.path.exists(last_data_path):
        return

    first_data = scada.fetch(config.get('urls','scada-sheet'))
    first_data.save(last_data_path)
    logging.info("Created %s" % last_data_path)

    if os.path.exists(new_data_path):
        return
    first_data.save(new_data_path)
    logging.info("Created %s" % new_data_path)

init_data()
last_data = DataSet.load(config.get('file-paths', 'last-data'))
new_data = DataSet.load(config.get('file-paths', 'new-data'))
