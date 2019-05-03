import numpy as np
import cv2
import datetime
from dateutil import parser
from os import listdir
from os.path import isfile, join
import json

min_chart_area = 200
path_frontlines = 'frontline'

def convert_contour(contour, convert_point):
    coords = []
    for points in contour:
        if len(points) != 1:
            print("ERROR")
        q = convert_point(points[0])
        coords.append((q[0], q[1]))
    return coords

def extract_contours(mask3, convert_point):
    #extract contours
    _, contours, hierarchy = cv2.findContours(mask3.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
    hierarchy = [] if hierarchy is None else hierarchy[0]

    #img_c = img.copy()
    #for contour in contours:
    #    area = cv2.contourArea(contour)
    #
    #    if area > min_chart_area:
    #        cv2.drawContours(img_c, contour, -1, (0, 255, 0), 2)
    #plt.imshow(img_c)
    #plt.show()

    #generate coordinate charts
    contour_paths = []
    top_level_contours = [(idx, x[2]) for idx, x in enumerate(hierarchy) if x[3] == -1]
    for contour_idx, first_child_idx in top_level_contours:
        area = cv2.contourArea(contours[contour_idx])
        if area < min_chart_area:
            continue
        next_child = first_child_idx
        child_contour_indices = []
        while next_child != -1:
            child_contour_indices.append(next_child)
            next_child = hierarchy[next_child][0]
        outer_coords = convert_contour(contours[contour_idx], convert_point)
        inner_list_coords = [convert_contour(contours[child_idx], convert_point) for child_idx in child_contour_indices]
        contour_paths.append((outer_coords, inner_list_coords))
    return contour_paths

def create_listfile():
    file_names = [f for f in listdir(path_frontlines) if isfile(join(path_frontlines, f))]
    data = [{"filename": f} for f in file_names if f != "frontline.json"]
    with open(join(path_frontlines, "frontline.json"), "w") as file:
        file.write(json.dumps(data))

def get_front_name(outer):
    x = [p[0] for p in outer]
    y = [p[1] for p in outer]
    centroid = np.array((sum(x) / len(outer), sum(y) / len(outer)))
    clusters = list({"West": (51.507222, -0.1275), "East": (52.246577, 21.012148), "South": (41.934977, 17.446289), "North": (57.7, 11.966667), "Africa": (33.651208, 15.46875)}.items())
    distances = [np.linalg.norm(centroid - np.array(cluster_center)) for name, cluster_center in clusters]
    min_idx = np.argmin(distances)
    return clusters[min_idx][0]

def save_frontline(date, contour_paths, additional_data = None, create_empty_for = [], ignore_fronts = []):
    data = [] if additional_data == None else additional_data.copy()
    for chart in contour_paths:
        front_name = get_front_name(chart[0])
        if front_name in ignore_fronts:
            continue
        q = {"fronts": [front_name], "outer": chart[0], "inner": chart[1]}
        data.append(q)

    #check that data contains fronts for all the ones listed in create_empty_for
    for front_name in create_empty_for:
        cnt = len([x for x in data if x["fronts"] == front_name]) != 0
        if not cnt:
            data.append({"fronts": front_name, "outer": [], "inner": []})

    name = parser.parse(date).date().isoformat()
    with open(join(path_frontlines, name + ".json"), "w") as file:
        file.write(json.dumps({"date": name, "charts": data}))