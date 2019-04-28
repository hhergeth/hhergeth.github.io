import csv
import json
from geopy.distance import geodesic
import datetime
import numpy as np
import dominate
from dominate.tags import *
from dominate.util import raw, text
from os import listdir
from os.path import isfile, join

def load_csv(filepath):
    with open(filepath) as csv_file:
        csv_reader = list(csv.reader(csv_file, skipinitialspace=True, delimiter=';'))
        for row in csv_reader[1:]:
            yield row

def load_places(filepath):
    items = list(load_csv(filepath))
    places = {}
    for item in items:
        coords = None
        if len(item) > 1 and item[1] != "":
            x = [x.strip() for x in item[1].split(',')]
            coords = (float(x[0]), float(x[1]))
        if item[0] in places:
            print(item[0] + " exists at least twice!")
        places[item[0]] = coords
    return places

# assigns coordinates to each 
def load_route(filepath, places):
    items = list(load_csv(filepath))
    route = []
    for item in items:
        date_s, place_name, annotations = item[0], item[1], None
        
        if len(item) > 2:
            annotations = item[2]
        else:
            annotations = "k"
        
        date = datetime.datetime.strptime(date_s, "%d.%m.%Y").date()
        if len(route) != 0 and date < route[-1][0]:
            print("Error, invalid date: ", date_s, place_name)
        coords = places[place_name]
        route.append((date, coords, place_name, annotations))

    # add missing coordinates
    for idx in range(len(route)):
        if route[idx][1] == None:
            coords_list = []
            if idx != 0 and route[idx - 1][1] != None:
                coords_list.append(np.array(route[idx - 1][1]))
            if idx != len(route) - 1 and route[idx + 1][1] != None:
                coords_list.append(np.array(route[idx + 1][1]))
            if len(coords_list) == 0:
                raise Error("No coordinates to average for : ", route[idx])
            coords = np.sum(coords_list, axis=0) / len(coords_list)

            q = list(route[idx])
            q[1] = (coords[0], coords[1])
            if not "o" in q[3]:
                q[3] = q[3] + "o"
            route[idx] = tuple(q)
    return route
    
def load_data_set(folder_name):
    places = load_places("data/" + folder_name + "/places.csv")
    route = load_route("data/" + folder_name + "/route.csv", places)
    return {"places": places, "route": route}
    
uv_s_00, uv_t_00 = np.array((58.7169, -3.3508)), np.array((58.5625, -2.9663))
uv_s_10, uv_t_10 = np.array((36.5185, 10.4919)), np.array((36.9916, 11.0852))
uv_s_11, uv_t_11 = np.array((34.6558, 32.9865)), np.array((34.9985, 33.1732))
uv_s_01, uv_t_01 = np.array((59.5844, 30.3442)), np.array((59.8117, 30.1245))

v_00 = (uv_t_00 - uv_s_00)
v_10 = 0.7*(uv_t_10 - uv_s_10)
v_11 = (uv_t_11 - uv_s_11)
v_01 = (uv_t_01 - uv_s_01)

def lerp(a, b, t):
    return a + (b - a) * t   
   
def adjust_point_late(p):
    latlng = np.array(p)
    tu1 = (latlng[1] - uv_s_00[1]) / (uv_s_01[1] - uv_s_00[1])
    tu2 = (latlng[1] - uv_s_10[1]) / (uv_s_11[1] - uv_s_10[1])
    y_bottom = lerp(uv_s_00[0], uv_s_01[0], tu1)
    y_top = lerp(uv_s_10[0], uv_s_11[0], tu2)
    tv = (latlng[0] - y_bottom) / (y_top - y_bottom)
    a = lerp(v_00, v_01, tu1)
    b = lerp(v_10, v_11, tu2)
    off = lerp(a, b, tv)
    q = latlng + off
    return (q[0], q[1])

data = {}
data["Hans Jürgen Hartmann"] = load_data_set("hartmann")
data["Günther Koschorrek"] = load_data_set("koschorrek")
data["Guy Sajer"] = load_data_set("sajer")
data["Hans von Luck"] = load_data_set("von Luck")

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.date):
            return o.isoformat()#strftime("%d.%m.%Y")

        return json.JSONEncoder.default(self, o)
person_data_json_string = json.dumps(data, cls=DateTimeEncoder)

frontline_data = []
mypath = "data/frontline"
frontline_data_sets = [f for f in listdir(mypath) if isfile(join(mypath, f))]
for filename_set in frontline_data_sets:
    with open(join(mypath, filename_set), 'r') as f:
        q = json.load(f)
        for date_s, points in q.items():
            date = datetime.datetime.strptime(date_s, "%Y-%m-%d").date()
            
            #adjust the points, they all have a slight offset
            if "-late" in filename_set:
                points = [[adjust_point_late(p) for p in points2] for points2 in points]
            
            frontline_data.append((date, points))

frontline_data_json_string = json.dumps(frontline_data, cls=DateTimeEncoder)
print("Number fronts :", len(frontline_data))

with open("page/data-frontline.js", "w") as js_file:
    js_file.write("var frontline_data = %s;" % frontline_data_json_string)
    
with open("page/data-persons.js", "w") as js_file:
    js_file.write("var data = %s;" % person_data_json_string)