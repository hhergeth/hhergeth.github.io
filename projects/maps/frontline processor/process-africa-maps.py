import numpy as np
import json
from os import listdir
from os.path import isfile, join
from utils import *

data_dir = 'data africa/'

with open(data_dir + "listfile.json", "r") as json_file:
    listfile = json.load(json_file)

for f in listfile:
    with open(data_dir + f['filename'], "r") as json_file:
        geofile = json.load(json_file)

    data = []
    for feature in geofile['features']:
        coords = feature['geometry']['coordinates']
        
        has2 = "cutoff2" in f
        coords2 = []
        for A in coords:
            B = []
            for point in A:
                if point[0] > f['cutoff'] or (has2 and point[0] < f['cutoff2']):
                    B.append([point[1], point[0]])
            coords2.append(B)
        
        data.append({"fronts": ['Africa'], "outer": coords2[0], "inner": coords2[1:]})

    date = f['filename'][:10]
    save_frontline(date, [], data)
create_listfile()