import cv2
import numpy as np
from matplotlib import pyplot as plt
from os import listdir
from os.path import isfile, join
import json
import sys
import datetime
from dateutil import parser
from scipy.optimize import minimize
import folium
from utils import *

cities_coordinates_deg = {"london": (51.507222, -0.1275),
                          "berlin": (52.516667, 13.388889),
                          "warsaw": (52.246577, 21.012148),
                          "belgrad": (44.816667, 20.466667),
                          "paris": (48.8567, 2.3508),
                          "leningrad": (59.9375, 30.308611),
                          "rostov": (47.233333, 39.7),
                          "moscow": (55.75, 37.616667),
                          "woronesch": (51.671667, 39.210556),
                          "odessa": (46.485722, 30.743444),
                          "istanbul": (41.013611, 28.955),
                          "tunis": (36.806389, 10.181667),
                          "rom": (41.9, 12.5),
                          "sewastopol": (44.6, 33.5333),
                          "helsinki": (60.170833, 24.9375),
                          "edinburgh": (55.953, -3.189),
                          "toulouse": (43.6045, 1.444),
                          "marseille": (43.2964, 5.37),
                          "gothenburg": (57.7, 11.966667),
                          "munich": (48.133333, 11.566667),
                          "perugia": (43.112222, 12.388889),
                          "riga": (56.948889, 24.106389),
                          "lwow": (49.83, 24.014167),
                          "nis": (43.32102, 21.89567)}

cities_early = ["london", "paris", "berlin", "rom", "tunis", "helsinki", "warsaw", "belgrad", "leningrad", "moscow", "woronesch", "rostov", "odessa", "sewastopol", "istanbul"]
cities_late = ["edinburgh", "london", "paris", "toulouse", "marseille", "gothenburg", "berlin", "munich", "perugia", "riga", "warsaw", "lwow", "belgrad"]

annotations_file_path = "image-annotations.json"
path_images = 'data'

with open("shape-gb.json", "r") as json_file:
    shape_gb = json.load(json_file)

if isfile(annotations_file_path):
    with open(annotations_file_path, "r") as json_file:
        annotations = json.load(json_file)
else:
    annotations = {}

def get_early(name):
    date = parser.parse(name[:10])
    return date < parser.parse('1944-12-01')

def compute_scale_factor(a_coords, a_point, b_coords, b_point):
    phi1, lmb0 = np.deg2rad(a_coords)
    phi, lmb = np.deg2rad(b_coords)
    c_correct = np.arccos(np.sin(phi1) * np.sin(phi) + np.cos(phi1) * np.cos(phi) * np.cos(lmb - lmb0))
    c_real = np.sqrt((b_point[0] - a_point[0])**2 + (b_point[1] - a_point[1])**2)
    return c_correct / c_real

def transform(c, x):
    return np.array([c[0] * x[0] + c[1] * x[1] + x[4], c[0] * x[2] + c[1] * x[3] + x[5]])

def convert_point(p, scale_factor, xq, p_berlin):
    p = transform(p, xq[:6])
    x,y = (p[0] - p_berlin[0]) * scale_factor, -(p[1] - p_berlin[1]) * scale_factor
    phi1, lmb0 = np.deg2rad(cities_coordinates_deg['berlin'])
    c = np.sqrt(x * x + y * y)
    phi = np.arcsin(np.cos(c) * np.sin(phi1) + (y * np.sin(c) * np.cos(phi1)) / (c))
    lbd = lmb0 + np.arctan2(x * np.sin(c), (c * np.cos(phi1) * np.cos(c) - y * np.sin(phi1) * np.sin(c)))
    q = np.array((np.rad2deg(phi), np.rad2deg(lbd)))
    return transform(q, xq[6:])

class Click():
    def __init__(self, ax, func, button=1):
        self.ax=ax
        self.func=func
        self.button=button
        self.press=False
        self.move = False
        self.c1=self.ax.figure.canvas.mpl_connect('button_press_event', self.onpress)
        self.c2=self.ax.figure.canvas.mpl_connect('button_release_event', self.onrelease)
        self.c3=self.ax.figure.canvas.mpl_connect('motion_notify_event', self.onmove)

    def onclick(self,event):
        if event.inaxes == self.ax:
            if event.button == self.button:
                self.func(event, self.ax)
    def onpress(self,event):
        self.press=True
    def onmove(self,event):
        if self.press:
            self.move=True
    def onrelease(self,event):
        if self.press and not self.move:
            self.onclick(event)
        self.press=False; self.move=False

def process_image(filepath, cities):
    img = cv2.imread(filepath)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.imshow(img)
    text=ax.text(0,0, "", va="bottom", ha="left")

    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')

    points = []
    def onclick(event, ps, fig, cities):
        ps.append((event.xdata, event.ydata))
        if len(ps) == len(cities):
            plt.close()
        fig.canvas.set_window_title(cities[len(ps)])

    click = Click(ax, lambda event,_: onclick(event, points, fig, cities), button=1)
    fig.canvas.set_window_title(cities[0])
    plt.show(block = True)
    return points

def mark():
    plt.switch_backend('TkAgg')

    file_names = [f for f in listdir(path_images) if isfile(join(path_images, f))]
    for name in file_names:
        if not name in annotations:
            early = get_early(name)

            cities = cities_early if early else cities_late
            q = process_image(join(path_images, name), cities)
            if len(q) != len(cities):
                print("did only select ", q, " but needed ", len(cities))
                return
            annotations[name] = q

            f = open(annotations_file_path, "w")
            f.write(json.dumps(annotations))
            f.close()

def process():
    #add the pre soviet war shapes
    fix_points = annotations["1943-11-15GerWW2BattlefrontAtlas.jpg"]
    annotations['1939-08-31.jpg'] = fix_points
    annotations['1939-09-27.jpg'] = fix_points
    annotations['1940-04-10.jpg'] = fix_points
    annotations['1940-06-10.jpg'] = fix_points
    annotations['1940-06-22.jpg'] = fix_points 
    annotations['1941-06-01.jpg'] = fix_points 

    for name, cities_points in annotations.items():
        early = get_early(name)
        cities_names = cities_early if early else cities_late
        cities_coords = [cities_coordinates_deg[city_name] for city_name in cities_names]
        filepath = join(path_images, name)

        if len(cities_points) != len(cities_coords):
            print("ERROR :", cities_points, cities_coords, cities_names)
            return

        #compute mask
        img = cv2.imread(filepath)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        fake_map = parser.parse(name[:10]) < parser.parse('1941-06-15')
        if not fake_map:
            #hsv_img2 = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
            #mask1 = hsv_img2[:,:,1].astype(int)
            #mask1 = cv2.inRange(mask1, 60 if early else 35, 255).astype(np.uint8)
            #
            #mask2 = hsv_img2[:,:,2]
            #mask2 = cv2.inRange(mask2, 30, 255).astype(np.uint8)
            #
            #mask3 = np.bitwise_and(mask1, mask2)
            #
            #kernel = np.ones((5,5), np.uint8)
            #se1 = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
            #se2 = cv2.getStructuringElement(cv2.MORPH_RECT, (7,7))
            #mask3 = cv2.morphologyEx(mask3, cv2.MORPH_OPEN, se1)
            #mask3 = cv2.morphologyEx(mask3, cv2.MORPH_CLOSE, se2)
            blur = cv2.blur(img,(5,5))
            hsv_img2 = cv2.cvtColor(blur, cv2.COLOR_RGB2HSV)
            mask3 = cv2.inRange(hsv_img2[:,:,1], 50, 255)
            se1 = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
            se2 = cv2.getStructuringElement(cv2.MORPH_RECT, (10,10))
            mask3 = cv2.morphologyEx(mask3, cv2.MORPH_OPEN, se1)
            mask3 = cv2.morphologyEx(mask3, cv2.MORPH_CLOSE, se2)
            #mask3 = cv2.dilate(mask3, np.ones((5,5),np.uint8), iterations=2)

            mask3[60:120,160:460]=0
        else:
            maskA = cv2.inRange(img[:,:,0], 0, 0)
            maskB = cv2.inRange(img[:,:,1], 0, 0)
            maskC = cv2.inRange(img[:,:,2], 0, 0)
            mask3 = np.bitwise_and(np.bitwise_and(maskA, maskB), maskC)
            mask3 = cv2.dilate(mask3, np.ones((5,5),np.uint8), iterations=1)

        #plt.imshow(mask3)
        #plt.show()

        #compute average scale factor
        idx_berlin = cities_names.index("berlin")
        scale_factors = []
        for idx in range(len(cities_names)):
            if cities_names[idx] != "berlin":
                scale_factors.append(compute_scale_factor(cities_coords[idx_berlin], cities_points[idx_berlin], cities_coords[idx], cities_points[idx]))
        scale_factor = sum(scale_factors) / len(scale_factors)

        #print(scale_factors, scale_factor)

        #find best mapping
        def fopt(x):
            s = 0.0
            for i in range (len(cities_names)):
                if i != idx_berlin:
                    c = convert_point(cities_points[i], scale_factor, x, cities_points[idx_berlin])
                    s += np.sqrt(abs(cities_coords[i][0] - c[0])**2 + abs(cities_coords[i][1] - c[1])**2)
            return s
        x_id = [1, 0, 0, 1, 0, 0] + [1, 0, 0, 1, 0, 0]
        opt = minimize(fopt, x_id, method = 'SLSQP', options={'maxiter':10000})
        xopt = opt.x

        #print(opt)

        def cnv_point(p):
            return convert_point(p, scale_factor, xopt, cities_points[idx_berlin])
        contour_paths = extract_contours(mask3, cnv_point)

        # the fake ones are missing the gb shape and also need North and East fronts
        save_frontline(name[:10], contour_paths, shape_gb if fake_map else [], ['North', 'East', 'South'] if fake_map else [], [] if fake_map else ["Africa"])
    create_listfile()


if len(sys.argv) == 2 and sys.argv[1] == 'mark':
    mark()
elif len(sys.argv) == 2 and sys.argv[1] == 'process':
    process()