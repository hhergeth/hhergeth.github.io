import cv2
import numpy as np
from matplotlib import pyplot as plt
import json
from os import listdir
from os.path import isfile, join
from sklearn import linear_model
from sklearn.linear_model import MultiTaskLassoCV
import csv
from utils import *
import scipy as sp

with open("shape-gb.json", "r") as json_file:
    shape_gb = json.load(json_file)

with open('early-city-coordinates.csv', 'r') as csvFile:
    reader = csv.reader(csvFile)
    coordinates = [((int(row[1][2:]), int(row[2][1:-1])), (float(row[3][1:]), float(row[4][1:]))) for row in reader]
xdata = [x for x,y in coordinates]
ydata = [y for x,y in coordinates]
clf = linear_model.Lasso(alpha=0.1)
clf.fit(xdata, ydata)
def convert_point_clf(p):
    return clf.predict([p])[0]

points = np.array([p for p, c in coordinates])
coordinates = np.array([c for p, c in coordinates])
x_min, x_max = 200, 900
y_min, y_max = 200, 720
step = 1
grid_x, grid_y = np.mgrid[x_min:x_max:step, y_min:y_max:step]
x, y = grid_x[:,0], grid_y[0,:]
grid_z2 = sp.interpolate.griddata(points, coordinates, (grid_x, grid_y), method='linear')
def convert_point(p):
    q = sp.interpolate.interpn((x, y), grid_z2, p, "linear", False, None)[0]
    if np.isnan(q).any():
        return convert_point_clf(p)
    return q

front_data = {}
mypath = "data2"
files = [f for f in listdir(mypath) if isfile(join(mypath, f))]
for img_file_name in files:
    img = cv2.imread(join(mypath, img_file_name))
    ret2,mask1 = cv2.threshold(img,0,255,cv2.THRESH_BINARY_INV)
    kernel = np.ones((3,3), np.uint8) 
    mask1 = cv2.dilate(mask1, kernel, iterations=1)
    mask1 = cv2.erode(mask1, kernel, iterations=1)
    mask1 = mask1[:,:,0].copy()
    
    contour_paths = extract_contours(mask1, convert_point)

    save_frontline(img_file_name[:10], contour_paths, shape_gb)

create_listfile()