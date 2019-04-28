import cv2
import numpy as np
from matplotlib import pyplot as plt
from os import listdir
from os.path import isfile, join
import json

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

def process_image(filepath):
    img = cv2.imread(filepath)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.imshow(img)
    text=ax.text(0,0, "", va="bottom", ha="left")
    
    points = []
    def onclick(event, ps):
        if len(ps) <= 1:
            ps.append((event.xdata, event.ydata))
        if len(ps) == 2:
            plt.close()
    click = Click(ax, lambda event,_: onclick(event, points), button=1)
    plt.show(block = True)
    return points
    
mypath = "data"
coordinates = {f : process_image(join(mypath, f)) for f in listdir(mypath) if isfile(join(mypath, f))}
f = open("locations.json", "w")
f.write(json.dumps(coordinates))
f.close()