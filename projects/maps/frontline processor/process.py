import cv2
import numpy as np
from matplotlib import pyplot as plt
import json

with open("locations.json", 'r') as f:
    coordinates_data = json.load(f)

front_data = {}

for img_file_name, coordinates in coordinates_data.items():
    p_berlin, p_warsaw = coordinates[0], coordinates[1]
    c_berlin = (np.deg2rad(52.516667), np.deg2rad(13.388889))
    c_warsaw = (np.deg2rad(52.246577), np.deg2rad(21.012148))
    
    img = cv2.imread("data/" + img_file_name)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    hsv_img2 = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    q = (hsv_img2[:,:,0].astype(int) + 20) % 180
    mask1 = cv2.inRange(q, 0, 40)

    kernel = np.ones((5,5), np.uint8) 
    mask1 = cv2.erode(mask1, kernel, iterations=1)
    mask1 = cv2.dilate(mask1, kernel, iterations=2)
    image, contours, hierarchy = cv2.findContours(mask1,cv2.RETR_LIST,cv2.CHAIN_APPROX_TC89_KCOS)
    
    if len(contours) == 0:
        plt.figure(num=img_file_name)
        plt.imshow(mask1)
        plt.show()
        print(img_file_name)
    
    phi1, lmb0 = c_berlin
    phi, lmb = c_warsaw
    c_correct = np.arccos(np.sin(phi1) * np.sin(phi) + np.cos(phi1) * np.cos(phi) * np.cos(lmb - lmb0))
    c_real = np.sqrt((p_warsaw[0] - p_berlin[0])**2 + (p_warsaw[1] - p_berlin[1])**2)
    scale_factor = c_correct / c_real
    
    def convert_point(p):
        x,y = (p[0] - p_berlin[0]) * scale_factor, -(p[1] - p_berlin[1]) * scale_factor
        phi1, lmb0 = c_berlin
        c = np.sqrt(x * x + y * y)
        phi = np.arcsin(np.cos(c) * np.sin(phi1) + (y * np.sin(c) * np.cos(phi1)) / (c))
        lbd = lmb0 + np.arctan2(x * np.sin(c), (c * np.cos(phi1) * np.cos(c) - y * np.sin(phi1) * np.sin(c)))
        latlng = np.array((np.rad2deg(phi), np.rad2deg(lbd)))
        
        #tu1 = (latlng[1] - uv_s_00[1]) / (uv_s_01[1] - uv_s_00[1])
        #tu2 = (latlng[1] - uv_s_10[1]) / (uv_s_11[1] - uv_s_10[1])
        #y_bottom = lerp(uv_s_00[0], uv_s_01[0], tu1)
        #y_top = lerp(uv_s_10[0], uv_s_11[0], tu2)
        #tv = (latlng[0] - y_bottom) / (y_top - y_bottom)
        #a = lerp(v_00, v_01, tu1)
        #b = lerp(v_10, v_11, tu2)
        #off = lerp(a, b, tv)
        return latlng# + off

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
    
f = open("front-data.json", "w")
f.write(json.dumps(front_data))
f.close()