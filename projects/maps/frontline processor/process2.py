import cv2
import numpy as np
from matplotlib import pyplot as plt
import json
from os import listdir
from os.path import isfile, join
from sklearn import linear_model
from sklearn.linear_model import MultiTaskLassoCV
import csv

with open('coordinates.csv', 'r') as csvFile:
    reader = csv.reader(csvFile)
    coordinates = [((int(row[1][2:]), int(row[2][1:-1])), (float(row[3][1:]), float(row[4][1:]))) for row in reader]
xdata = [x for x,y in coordinates]
ydata = [y for x,y in coordinates]
clf = linear_model.Lasso(alpha=0.1)
clf.fit(xdata, ydata)

#from scipy import interpolate
#fx = interpolate.interp2d([x for x,y in xdata], [y for x,y in xdata], [x for x,y in ydata], kind='cubic')
#fy = interpolate.interp2d([x for x,y in xdata], [y for x,y in xdata], [y for x,y in ydata], kind='cubic')
#
#def unproject(p):
#    return np.array([fx(*p)[0], fy(*p)[0]])

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
    image, contours, hierarchy = cv2.findContours(mask1,cv2.RETR_LIST,cv2.CHAIN_APPROX_TC89_KCOS)
    
    if len(contours) == 0:
        plt.figure(num=img_file_name)
        plt.imshow(mask1)
        plt.show()
        print(img_file_name)
    
    def convert_point(p):
        return clf.predict([p])[0]
        #q = unproject(p)
        #return (q[0], q[1])
   
    contour_paths = []
    for contour in contours:
        area = cv2.contourArea(contour)
        latlng_points = []
        if area > 500:
            for points in contour:
                if len(points) != 1:
                    print("ERROR")
                q = convert_point(points[0])
                latlng_points.append((q[0], q[1]))
            contour_paths.append(latlng_points)
            
    timestamp = img_file_name[:10]
    front_data[timestamp] = contour_paths
    
f = open("front-data-early.json", "w")
f.write(json.dumps(front_data))
f.close()