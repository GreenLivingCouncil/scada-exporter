import scada
from utils import config
from models import DataSet
ds = scada.fetch(config.get('urls','scada-sheet'))

print ds 
ds.save('test.json')

print DataSet.load('test.json')

