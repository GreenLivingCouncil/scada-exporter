"""The data objects."""
import datetime

class BuildingNode(object):
    """Simple class to extract building info from XML node."""
    def __init__(self, name, error=None, kwh=None, kw=None):
        self.name = name
        self.error = error
        self.kwh = kwh
        self.kw = kw

    @staticmethod
    def combine(combined_name, buildings):
        # skip if there is a hole in the constituent data
        # TODO actually report which building had the error
        if any(building.error for building in buildings):
            return BuildingNode(
                combined_name,
                error="Error in constituent building meter (at least one of %s)." % ", ".join(parts)
            )
        else:
            return BuildingNode(
                combined_name,
                kwh=sum(building.kwh for building in buildings),
                kw=sum(building.kw for building in buildings)
            )

class DataSetDelta(object):
    pass

class DataSet(object):
    def __init__(self, buildings, date=datetime.datetime.now()):
        self.buildings = buildings
        self.date = date

    def save(self, json_path):
        """Save to JSON file."""
        data_dict = {
            "date": self.date.strftime(DT_FORMAT),
            "data": self.buildings
        }
        with open(json_path, 'w') as dest_f:
            json.dump(data_dict, dest_f, indent=4, sort_keys=True)

    @staticmethod
    def load(json_path):
        """Load from JSON file."""
        with open(json_path) as src_f:
            data_dict = json.load(src_f)
            return DataSet(data_dict["data"], data_dict["date"])

