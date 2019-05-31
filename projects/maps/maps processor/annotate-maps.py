import cv2
import numpy as np
from matplotlib import pyplot as plt
from os import listdir
from os.path import isfile, join
import json
import re
import sys

annotations_file_path = "map-annotations.json"
input_folder_path = "input maps"

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

def save_annotations(annotations):
    with open(annotations_file_path, "w") as f:
        f.write(json.dumps(annotations, indent=4))

def process_image(filepath, num_points):
    img = cv2.imread(filepath)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed') #works fine on Windows!
    plt.imshow(img)
    text=ax.text(0,0, "", va="bottom", ha="left")
    fig.canvas.set_window_title(filepath)

    points = []
    def onclick(event, ps):
        if len(ps) <= num_points - 1:
            ps.append((event.xdata, event.ydata))
        if len(ps) == num_points:
            plt.close()
        print(ps)
    click = Click(ax, lambda event,_: onclick(event, points), button=1)
    plt.show(block = True)
    return points

if isfile(annotations_file_path):
    with open(annotations_file_path, "r") as json_file:
        annotations = json.load(json_file)
else:
    annotations = {}

if len(sys.argv) == 1:
    p = re.compile("([a-zA-Z]\d\d)")
    for file_path in listdir(input_folder_path):
        name = file_path.replace(".jpg", "")
        if isfile(join(input_folder_path, file_path)) and not name in annotations and not "desktop.ini" in file_path:
            points = process_image(join(input_folder_path, file_path), 4)
            result = p.search(file_path)
            loc = result.group(1).capitalize() if result else "???"
            annotations[name] = (loc, points)
            save_annotations(annotations)
else:
    # input points horizontally
    file_path = sys.argv[1]
    num_v, num_h = int(sys.argv[2]), int(sys.argv[3])
    tile_name_lat, tile_names_lng = int(sys.argv[4]), sys.argv[5:]
    if num_h != len(tile_names_lng):
        print("Error, num_v != len(tile_names_lng), ", num_h, tile_names_lng)
        sys.exit()

    points_all = process_image(join(input_folder_path, file_path), (num_v + 1) * (num_h + 1))
    for hor in range(0, num_h):
        for ver in range(0, num_v):
            idx = hor * (num_v + 1) + ver
            points = points_all[idx : idx + 2] + points_all[idx + (num_v + 1) : idx + (num_v + 1) + 2]
            map_name = tile_names_lng[hor] + str(tile_name_lat - ver)
            annotations[map_name] = (map_name, points)
    save_annotations(annotations)