import json
import os
import cv2
import numpy as np
import mercantile
from PIL import Image
from skimage.transform import ProjectiveTransform
import pathlib

def lerp(a, b, t):
    return a + (b - a) * t

def decode_map_location(loc_string):
    real_loc = loc_string
    if not loc_string[0].isdigit():
        q = ord(loc_string[0])
        if q >= ord('G'):
            idx1 = q - ord('G')
            if q < ord('I'):
                idx1 = idx1 + 1
        else:
            idx1 = q - ord('A') + 20
        idx2 = int(loc_string[1:])
    else:
        idx1 = ord('G') - ord('A') + 20 + int(loc_string[0])
        idx2 = int(loc_string[1:])
        real_loc = ['G', 'H', 'I', 'II', 'III', 'IV', 'V'][int(loc_string[0])] + loc_string[1:]

    lng = -2 + 1 / 3 + idx1 * 2
    lat = idx2
    return lat, lng, real_loc

# returns top_left, top_right, bottom_right, bottom_left
def sort_points(points, w, h):
    def find_min(p):
        distances = [np.linalg.norm(np.array(p)-np.array(b)) for b in points]
        index_min = np.argmin(distances)
        return points[index_min]

    return [find_min([0,0]), find_min([w, 0]), find_min([w, h]), find_min([0, h])]

def get_tile_path(tile_folder_path, z, x, y):
    tile_path = tile_folder_path + "/" + str(z) + "/" + str(x) + "/" + str(y) + ".png"
    p = pathlib.Path(tile_path).parent
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)
    return tile_path

def load_or_create_tile(tile_path):
    if os.path.isfile(tile_path):
        tile_img = Image.open(tile_path)
    else:
        tile_img = Image.new("RGB", (256, 256))
    return tile_img

class QuadMapping:
    def __init__(self, points, lat, lng):
        self.lat = lat
        self.lng = lng
        self.t = ProjectiveTransform()
        if not self.t.estimate(np.array(points), np.asarray([[lat, lng], [lat, lng + 2], [lat - 1, lng + 2], [lat - 1, lng]])): raise Exception("estimate failed")

    def map_pixel_to_geo(self, P):
        q = self.t(np.array(P)).flatten()
        return np.array([np.clip(q[0], self.lat - 1, self.lat), np.clip(q[1], self.lng, self.lng + 2)])

    def map_geo_to_pixel(self, lat, lng):
        lat, lng = np.clip(lat, self.lat - 1, self.lat), np.clip(lng, self.lng, self.lng + 2)
        q = self.t.inverse(np.array([lat, lng]))
        return q.flatten()

def process_map(zoom_level, tile_folder_path, img, img_path, lat_img, lng_img, img_corners):
    quad_mapping = QuadMapping(img_corners, lat_img, lng_img)

    # compute tiles
    tiles = mercantile.tiles(lng_img, lat_img - 1, lng_img + 2, lat_img, zoom_level)
    parents_tiles = []
    for tile in tiles:
        lng_tile, lat_tile = mercantile.ul(tile)
        lng_next, lat_next = mercantile.ul(mercantile.Tile(x=tile.x + 1, y=tile.y + 1, z=zoom_level))

        def to_tile_pixel(lat, lng):
            tile_x = (lng - lng_tile) / (lng_next - lng_tile)
            tile_y = (lat - lat_next) / (lat_tile - lat_next)
            tile_x = np.clip(tile_x, 0, 1)
            tile_y = np.clip(tile_y, 0, 1)
            return int(round(tile_x * 255)), int(round((1 - tile_y) * 255))

        tile_corners = [quad_mapping.map_geo_to_pixel(lat_tile, lng_tile), quad_mapping.map_geo_to_pixel(lat_tile, lng_next), quad_mapping.map_geo_to_pixel(lat_next, lng_next), quad_mapping.map_geo_to_pixel(lat_next, lng_tile)]
        q00, q11 = quad_mapping.map_pixel_to_geo(tile_corners[0]), quad_mapping.map_pixel_to_geo(tile_corners[2])
        p00, p11 = to_tile_pixel(*q00), to_tile_pixel(*q11)
        dest_width, dest_height = p11[0] - p00[0] + 1, p11[1] - p00[1] + 1
        tile_pixel_x, tile_pixel_y = p00

        LL = tile_corners[0].tolist() + tile_corners[3].tolist() + tile_corners[2].tolist() + tile_corners[1].tolist()
        crop_img = img.transform((dest_width, dest_height), Image.QUAD, LL)
        tile_path = get_tile_path(tile_folder_path, tile.z, tile.x, tile.y)
        tile_img = load_or_create_tile(tile_path)
        tile_img.paste(crop_img, (tile_pixel_x, tile_pixel_y))
        tile_img.save(tile_path, format="PNG", quality=85)

        parents_tiles.append(mercantile.parent(tile))
    return parents_tiles

def compute_mipmap_layer(zoom_level, tile_folder_path, input_tiles):
    input_tiles = set(input_tiles)
    output_tiles = []
    for tile in input_tiles:
        if zoom_level != 0:
            output_tiles.append(mercantile.parent(tile))
        def load_child_img(xoff, yoff):
            x, y = tile.x * 2 + xoff, tile.y * 2 + yoff
            tile_path = get_tile_path(tile_folder_path, zoom_level + 1, x, y)
            return load_or_create_tile(tile_path)
        img00 = load_child_img(0, 0)
        img10 = load_child_img(1, 0)
        img11 = load_child_img(1, 1)
        img01 = load_child_img(0, 1)
        result = Image.new("RGB", (512, 512))
        result.paste(img00, (0, 0))
        result.paste(img10, (256, 0))
        result.paste(img11, (256, 256))
        result.paste(img01, (0, 256))

        tile_path = get_tile_path(tile_folder_path, zoom_level, tile.x, tile.y)
        result = result.resize((256, 256))
        result.save(tile_path, format="PNG", quality=85)

    return output_tiles

tile_folder_path = "C:/Users/hherg/Desktop/historic tiles"
annotations_file_path = "map-annotations.json"
input_folder_path = "input maps"
processed_file_path = "processed-tiles.json"
zoom_level = 12

if os.path.isfile(processed_file_path):
    with open(processed_file_path, "r") as json_file:
        processed_maps = json.load(json_file)
else:
    processed_maps = {}

with open(annotations_file_path, "r") as json_file:
    annotations = json.load(json_file)

parents_tiles = []
for map_name, annotation in annotations.items():
    if map_name in processed_maps:
        continue
    print("Processing map: ", map_name)

    map_file_path = os.path.join(input_folder_path, map_name + ".jpg")
    lat,lng, _ = decode_map_location(annotation[0])

    img = cv2.imread(map_file_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    height, width, channels = img.shape

    pixel_points = sort_points(annotation[1], width, height)

    parents_tiles += process_map(zoom_level, tile_folder_path, Image.fromarray(img), map_file_path, lat, lng, pixel_points)
    processed_maps[map_name] = []

 # the zoom level to compute tiles for
curr_zoom_level = zoom_level - 1
while curr_zoom_level >= 0:
    parents_tiles = compute_mipmap_layer(curr_zoom_level, tile_folder_path, parents_tiles)
    curr_zoom_level = curr_zoom_level - 1

map_annotations = []
for map_name, annotation in annotations.items():
    lat,lng, map_quad = decode_map_location(annotation[0])
    map_annotations.append(annotation[0])

with open(tile_folder_path + '/map_annotations.js', "w") as json_file:
    json_file.write("historic_maps_processed = " + json.dumps(map_annotations, indent=4))

with open(processed_file_path, "w") as json_file:
    json_file.write(json.dumps(processed_maps, indent=4))