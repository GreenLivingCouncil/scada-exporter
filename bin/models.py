"""The data objects."""
import datetime
import json

# Datetime Format
DT_FORMAT = "%m/%d/%Y %H:%M:%S"

class Building(object):
    """Simple class to extract building info from XML node."""
    def __init__(self, name, error=None, kwh=None, kw=None):
        # Semantics of kwh and kw are undefined when error is set.
        self.name = name
        self.error = error
        self.kwh = kwh
        self.kw = kw

    @staticmethod
    def combine(combined_name, buildings):
        # skip if there is a hole in the constituent data
        # TODO actually report which building had the error
        if any(building.error for building in buildings):
            return Building(
                combined_name,
                error="Error in constituent building meter (at least one of %s)." % ", ".join(parts)
            )
        else:
            return Building(
                combined_name,
                kwh=sum(building.kwh for building in buildings),
                kw=sum(building.kw for building in buildings)
            )

    def __repr__(self):
        return "%s(%r, %r, %r, %r)" % (self.__class__.__name__, self.name, self.error, self.kwh, self.kw)

class DataSet(object):
    def __init__(self, buildings, date=datetime.datetime.now()):
        self.buildings = buildings
        self.date = date

    def apply_combinations(self, combine_defs):
        for combination, parts in combine_defs.iteritems():
            self.buildings[combination] = Building.combine(combination, [self.buildings[p] for p in parts])

    def save(self, json_path):
        """Save to JSON file."""
        data_dict = {
            "date": self.date.strftime(DT_FORMAT),
            "data": [building.__dict__ for building in self.buildings.itervalues()]
        }
        with open(json_path, 'w') as dest_f:
            json.dump(data_dict, dest_f, indent=4, sort_keys=True)

    @staticmethod
    def load(json_path):
        """Load from JSON file."""
        with open(json_path) as src_f:
            data_dict = json.load(src_f)
            date = datetime.datetime.strptime(data_dict["date"], DT_FORMAT)
            buildings_list = [Building(**building) for building in data_dict["data"]]
            buildings = dict((building.name, building) for building in buildings_list)
            return DataSet(buildings, date)

    def __repr__(self):
        return "DataSet(%r, %r)" % (self.date, self.buildings.values())

