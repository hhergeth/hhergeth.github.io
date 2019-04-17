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

distinct_colors = ['#ffe119', '#3cb44b', '#e6194B', '#4363d8', '#f58231', '#469990', '#f032e6', '#fabebe']
doc = dominate.document(title="Maps")
with doc.head:
    script(type='text/javascript', src='data-frontline.js')
    script(type='text/javascript', src='data-persons.js')

    script(type='text/javascript', src='moment.min.js')
    script(type='text/javascript', src='lightpick.js')
    script(type='text/javascript', src='leaflet/leaflet.js')
    script(type='text/javascript', src='leaflet/leaflet.polylineDecorator.js')
    script(type='text/javascript', src='leaflet/leaflet.textpath.js')
    script(type='text/javascript', src='Leaflet-MiniMap/Control.MiniMap.min.js')
    script(type='text/javascript', src='leaflet-measure-path.js')
    link(rel='stylesheet', href='leaflet/leaflet.css')
    link(rel='stylesheet', href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css')
    link(rel='stylesheet', href='lightpick.css')
    link(rel='stylesheet', href='Leaflet-MiniMap/Control.MiniMap.min.css')
    link(rel='stylesheet', href='leaflet-measure-path.css')
    raw('''
<style>
body {
    padding: 0;
    margin: 0;
}
html, body, #map {
    height: 100%;
    width: 100%;
}
.legend {
    line-height: 18px;
    color: #555;
}
.legend i {
    width: 35px;
    height: 6px;
    float: left;
    margin-top: 6px;
    margin-right: 8px;
    opacity: 1.0;
}
</style>
''')

with doc:
    div(id="map")
    raw('''
<div id="date-element">
    <button style="font-size:15px" onclick="btn_change_date(0, -1, 'days')">&lt;</button>
    <button style="font-size:15px" onclick="btn_change_date(0, -1, 'months')">&lt;&lt;</button>
    <input class="date-picker" id="pick1">
    <button style="font-size:15px" onclick="btn_change_date(0, +1, 'months')">>></button>
    <button style="font-size:15px" onclick="btn_change_date(0, +1, 'days')">></button>
    <button style="font-size:15px" onclick="btn_right()" id="btn_right"><i class="fa fa-arrow-right"></i></button>
    <button style="font-size:15px" onclick="btn_link(this)" id="btn_link"><i class="fa fa-link"></i></button>
    <button style="font-size:15px" onclick="btn_left()" id="btn_left"><i class="fa fa-arrow-left"></i></button>
    <button style="font-size:15px" onclick="btn_change_date(1, -1, 'days')">&lt;</button>
    <button style="font-size:15px" onclick="btn_change_date(1, -1, 'months')">&lt;&lt;</button>
    <input class="date-picker" id="pick2">
    <button style="font-size:15px" onclick="btn_change_date(1, +1, 'months')">>></button>
    <button style="font-size:15px" onclick="btn_change_date(1, +1, 'days')">></button>
</div>
''')
    raw('''
<script>
var year_colors = %s;
var picker = null;
var map = null;
var person_groups = [];
var frontline_group = null;
var person_colors = ["green", "blue", "orange", "violet", "black"];

var storage  = window.localStorage;

function get_dash(annotations) {
    var dashes = null;
    if(annotations.includes("k"))
        dashes = "1, 0";
    if(annotations.includes("v"))
        dashes = "4, 24";
    if(annotations.includes("f"))
        dashes = "5, 5";
    if(annotations.includes("u"))
        dashes = "40, 10";
    if(annotations.includes("t"))
        dashes = "20, 30";
    return dashes;
}

function add_transition(latlng1, latlng2, date1, date2, colorf, annotations, group) {
    var opacity_line = 1.0;
    if(annotations.includes("?") || annotations.includes("o") || annotations.includes("z"))
        opacity_line = 0.75;

    var dashes = get_dash(annotations);
        
    var line = L.polyline([latlng1, latlng2], {
        color: colorf,
        opacity: opacity_line,
        dashArray: dashes,
        showMeasurements: true,
        //measurementOptions: { showOnHover: true }
    }).addTo(group);

    line.formatDistance = function(d) {
        var unit, distance_text;
        if (d > 1000) {
            d = d / 1000;
            unit = 'km';
        } else {
            unit = 'm';
        }

        if (d < 100) {
            distance_text = d.toFixed(1) + ' ' + unit;
        } else {
            distance_text = Math.round(d) + ' ' + unit;
        }
        
        var f = 'D.M';
        return moment(date1).format(f) + " - " + distance_text + " - " + moment(date2).format(f);
    }
    
    var arrowHead = L.polylineDecorator(line, {
        patterns: [
            {
                offset: '100%%',
                repeat: 0,
                symbol: L.Symbol.arrowHead({pixelSize: 18, polygon: false, pathOptions:{
                    stroke: true,
                    color: colorf,
                    opacity: opacity_line,
                }})
            }
        ]
    }).addTo(group);
}

function legend_transit(a, text) {
    return '<svg height="12" width="43"> <g fill="none" stroke="black" stroke-width="4"> <path stroke-dasharray="' + get_dash(a) + '" d="M0 7 L35 7"></path></g> </svg>' + text;
}

function closest_front(total, front, date) {
    var date_new_front = new Date(front[0]);
    if(date < date_new_front)
        return total;
    if(total == null)
        return front;
    var date_total_front = new Date(total[0]);
    var difference_ms_new = date - date_new_front;
    var difference_ms_total = date - date_total_front;
    return difference_ms_new < difference_ms_total ? front : total;
}

function plot(date_start, date_end) {    
    var person_idx = 0;
    for (var person_name in data) {
        var places = data[person_name].places;
        var route = data[person_name].route;
        
        var transitions_group = new L.featureGroup();
        var places_group = new L.featureGroup();
        
        var used_places = new Set();
        
        for (var idx = 0; idx < route.length - 1; idx++) {
            var coords1 = route[idx + 0][1];
            var coords2 = route[idx + 1][1];
            var date1 = route[idx + 0][0];
            var date2 = route[idx + 1][0];
            var name1 = route[idx + 0][2];
            var name2 = route[idx + 1][2];
            
            if(!(new Date(date1) <= date_end && date_start <= new Date(date2)))
                continue;

            var color = year_colors[new Date(date1).getFullYear() - 1939];
            add_transition(coords1, coords2, date1, date2, color, route[idx + 1][3], transitions_group);
            
            used_places.add(name1);
            used_places.add(name2);
        }
        
        var person_icon = new L.Icon({
            iconUrl: 'https://cdn.rawgit.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-' + person_colors[person_idx] + '.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        });
        
        for (let  place_name of used_places) {
            var latlng = places[place_name];
            if(latlng != null) {
                var marker = L.marker(latlng, {
                    title: place_name,
                    icon: person_icon
                }).addTo(places_group).bindPopup(place_name);
            }
        }
        
        person_group = person_groups[person_name];
        person_group.clearLayers();
        places_group.addTo(person_group);
        transitions_group.addTo(person_group);
        
        person_idx = person_idx + 1;
    }
    
    frontline_group.clearLayers();
    let front_start = frontline_data.reduce((total, v) => closest_front(total, v, date_start), null);
    let front_end = frontline_data.reduce((total, v) => closest_front(total, v, date_end), null);
    var fronts = new Set([front_start, front_end]);
    for (let front of fronts) {
        if(front == null)
            continue;
        for(idx = 0; idx < front[1].length; idx++)
            /*var polyline = L.polyline(front[1][idx]).addTo(frontline_group);*/
            var polygon = L.polygon(front[1][idx], {color: 'red', opacity: 0.25}).addTo(frontline_group);
    }
    
}
    
window.onload=function(){
    var osm = L.tileLayer('https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png', {
        maxZoom: 18,
    });

    map = L.map('map', {
        zoomControl: false,
        attributionControl: false
    }).addLayer(osm);
    map.doubleClickZoom.disable();

    for (var person_name in data) {
        var person_group = L.layerGroup();
        person_group.setZIndex(1);
        person_group.addTo(map);
        person_groups[person_name] = person_group;
    }
    frontline_group = new L.featureGroup();
    frontline_group.setZIndex(0);
    frontline_group.addTo(map);
    person_groups["HKL"] = frontline_group;
    
    var start_date = storage.getItem("start-date");
    if(start_date == null)
        start_date = "1939-01-01";
    start_date = new Date(start_date);
    var end_date = storage.getItem("end-date");
    if(end_date == null)
        end_date = "1950-01-01";
    end_date = new Date(end_date);
    
    plot(start_date, end_date);
    
    person_groups_html = [];
    var idx = 0;
    for(var entry_name in person_groups) {
        var color_name = "red";
        if(entry_name != "HKL") {
            color_name = person_colors[idx];
            idx = idx + 1;
        }
        var html_name = '<span style="color:' + color_name + '">' + entry_name + '</span>';
        person_groups_html[html_name] = person_groups[entry_name]
    }    
    L.control.layers(null, person_groups_html,{collapsed:false, position: 'bottomleft'}).addTo(map);
    
    var global_bbox = null;
    map.eachLayer(function (layers) {
        if (!(typeof layers.eachLayer === 'function'))
            return;
    
        layers.eachLayer(function (layer) {
            var b = layer.getBounds();
            if(global_bbox == null)
                global_bbox = b;
            else global_bbox = global_bbox.extend(b);
        });
    });
    
    map.fitBounds(global_bbox);
        
    /*L.control.scale({maxWidth: 200, position: 'bottomright'}).addTo(map);*/
    
    var legend = L.control({position: 'topright'});
    legend.onAdd = function(map) {
        var div = L.DomUtil.create('div', 'info legend');
        
        /* years */
        var labels = ['<strong>Years</strong>'];
        for (var i = 0; i < year_colors.length; i++) {
            labels.push('<i style="background:' + year_colors[i] + '"></i> ' + (1939 + i));
        }
        
        /* dashes */
        labels.push("");
        labels.push('<strong>Transits</strong>');
        labels.push(legend_transit("k", "Fight"));
        labels.push(legend_transit("v", "Hurt "));
        labels.push(legend_transit("f", "Run  "));
        labels.push(legend_transit("u", "Leave"));
        labels.push(legend_transit("t", "Trst "));
        
        div.innerHTML = labels.join('<br>');
        return div;
    };
    legend.addTo(map);
    
    var timeselector = L.control({position: 'topleft'});
    timeselector.onAdd = function(map) {        
        return document.getElementById("date-element");
    };
    timeselector.addTo(map);
    
    picker = new Lightpick({
        field: document.getElementById('pick1'),
        secondField: document.getElementById('pick2'),
        singleDate: false,
        repick: true,
        startDate: start_date,
        endDate: end_date,
        onSelect: function(start, end){
            plot(picker.getStartDate().toDate(), picker.getEndDate().toDate());
            storage.setItem("start-date", picker.getStartDate().toDate().toISOString());
            storage.setItem("end-date", picker.getEndDate().toDate().toISOString());
        }
    });
    
    var osm2 = new L.TileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {minZoom: 0, maxZoom: 13, attribution: "" });
    var miniMap = new L.Control.MiniMap(osm2, {
        centerFixed: [50.666667, 17.933333],
        zoomLevelFixed: 2,
        width: 250,
        autoToggleDisplay: true,
    }).addTo(map);
}

function btn_link(btn) {
    btn.children[0].className = btn.children[0].className == "fa fa-unlink" ? "fa fa-link" : "fa fa-unlink";
}

function btn_change_date(idx_date, delta, ty) {
    if (event.ctrlKey)
        ty = ty == "days" ? "weeks" : "years";

    var start = picker.getStartDate().clone();
    var end = picker.getEndDate().clone();
    var linked = document.getElementById("btn_link").children[0].className == "fa fa-link";

    if(linked || idx_date == 0)
        start.add(delta, ty);

    if(linked || idx_date == 1)
        end.add(delta, ty);

    picker.setDateRange(start, end);
}

function btn_right() {
    var start = picker.getStartDate().clone();
    picker.setDateRange(start, start);
}

function btn_left() {
    var end = picker.getEndDate().clone();
    picker.setDateRange(end, end);
}
</script>
''' % (distinct_colors))

with open("page/map.html", "w") as html_file:
    html_file.write(str(doc))

with open("page/data-frontline.js", "w") as js_file:
    js_file.write("var frontline_data = %s;" % frontline_data_json_string)
    
with open("page/data-persons.js", "w") as js_file:
    js_file.write("var data = %s;" % person_data_json_string)