
from partition import get_segment, create_matrix_transform, sc, step_coefficients, base_step_stud
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import transform
from shapely.affinity import affine_transform
import matplotlib.pyplot as plt
import cv2
import numpy as np
import geopandas as gpd
import pandas as pd
from collections.abc import Iterable

def draw_world(world_shp):
    grids = []
    outlines = []
    for lon in range(0, 16):
        for lat in range(-3, 4):
            border, grid, anchors = get_segment(lon, lat)
            outlines.append({'parity': lon % 2, 'geometry': border})
            for line in grid:
                grids.append({'parity': -1, 'geometry': line})
    outlines = gpd.GeoDataFrame(outlines, geometry='geometry')
    world_gdf = gpd.read_file(world_shp)
    world_gdf['parity'] = -1
    s = world_gdf.append(gpd.GeoDataFrame(grids, geometry='geometry')).append(outlines)
    s.plot(column='parity')
    plt.axis('off')
    plt.savefig("output/world.png", bbox_inches=0)
    
def draw_box(world_shp, x, y):

    border, grid, anchors = get_segment(x, y)
    print(anchors)
    grids = []
    for line in grid:
        grids.append({'color': "#FFFFFF", 'geometry': line})

    bounds = gpd.GeoDataFrame([{'color': "#000088", 'geometry': border.convex_hull}], geometry='geometry', crs="EPSG:4326")
    lines = gpd.GeoDataFrame(grids, geometry='geometry', crs="EPSG:4326")
    lines.geometry = lines.buffer(0.1).clip(bounds)
    
    lines = lines.assign(color="#FFFFFF")
    world_gdf = gpd.read_file(world_shp).clip(bounds)
    world_gdf['color'] = "#00BB00"

    
    #s = bounds.append(world_gdf)
    s = pd.concat([bounds, world_gdf, lines])
    s.plot(color=s["color"])

    plt.axis("off")
    plt.axis("tight")
    plt.axis("image")
    plt.savefig("output/grid_{}_{}.png".format(x,y), bbox_inches="tight", pad_inches=0)
    return plt

def build_stretch_box(world_shp, x, y):

    border, grid, anchors, tf= get_segment(x, y)
    print(anchors)
    
    def shift_transform(i, j, k=None):
        if isinstance(i, Iterable):
            raise TypeError
        #scale y to [0:1]
        xp = i+x
        yp = j+y-0.5
        if y == -3:
            yp = yp + 1/3

        return tuple(filter(lambda a: a is not None, [xp, yp]))
        
        
    grids = []
    grids_tf = []
    for line in grid:
        grids.append({'color': "#FFFFFF", 'geometry': line})
        grids_tf.append({'color': "#FFFFFF", 'geometry': transform(shift_transform, transform(tf, line))})
        
    

    
    bounds = gpd.GeoDataFrame([{'color': "#000088", 'geometry': border.convex_hull}], geometry='geometry')
    lines = gpd.GeoDataFrame(grids, geometry='geometry')
    
    
    world_gdf = gpd.read_file(world_shp).clip(bounds)
    
    bounds_tf = gpd.GeoDataFrame([{'color': "#000088", 'geometry': transform(shift_transform, transform(tf, border.convex_hull))}], geometry='geometry', crs=None)
    lines_tf = gpd.GeoDataFrame(grids_tf, geometry='geometry', crs=None)
    lines_tf.geometry = lines_tf.buffer(0.01).clip(bounds_tf)
    lines_tf = lines_tf.assign(color="#FFFFFF")
    
    if len(world_gdf.index) > 0:
        world_geom = world_gdf.dissolve().geometry.item() #[list(world_gdf.geometry.exterior.iloc[row_id].coords) for row_id in range(world_gdf.shape[0])]
        world_tf = gpd.GeoDataFrame([{'color': "#00BB00", 'geometry': transform(shift_transform, transform(tf, world_geom))}], geometry='geometry', crs=None)
        return [bounds_tf, lines_tf, world_tf]
    else:
        return [bounds_tf, lines_tf, None]
        
    #TODO: Add tf to offset by x, y-0.5

def draw_stretch_box(world_shp, x, y):
    bounds, lines, world = build_stretch_box(world_shp, x, y)
    if world is not None:
        s = pd.concat([bounds, lines])
    else:
        s = pd.concat([bounds, lines, world])
    #s = bounds.append(world_gdf)
    
    #TODO - return s instead, plot in main to support full map.
    s.plot(color=s["color"])

    plt.axis("off")
    plt.axis("tight")
    plt.axis("image")
    plt.savefig("output/block_{}_{}.png".format(x,y), bbox_inches="tight", pad_inches=0)
    return plt
    

def warp_box(img, targets, target_width, target_height):
    im = cv2.imread(img)
    targets.append([target_width/2, target_height/2])
    width, height = im.shape[:2]
    im_bounds = [[0,0], [height, 0], [0, width], [height, width], [height/2, width/2]]
    print(im_bounds)
    print(targets)
    #This isn't actually the right approach, need something different (trapezoid transform)
    matrix, status = cv2.findHomography(np.float32(im_bounds), np.float32(targets))
    result = cv2.warpPerspective(im, matrix, (target_width,target_height))
    cv2.imshow("source", im)
    cv2.imshow("target", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
def draw_warp(world_shp, x, y):
    draw_box(world_shp, x, y)
    border, grid, anchors = get_segment(x, y)
    coefficients = step_coefficients[int(abs(y))][x%2]
    warp_box("output/grid_{}_{}.png".format(x,y), anchors, int(coefficients[0]*base_step_stud*sc), int(coefficients[2]*base_step_stud*sc))
    
def draw_stretch_world(world_shp):
    bounds = []
    lines = []
    worlds = []
    for lon in range(0, 16):
        for lat in range(-3, 4):
            bound, line, world = build_stretch_box(world_shp, lon, lat)
            bounds.append(bound)
            lines.append(line)
            if world is not None:
                worlds.append(world)
                
    worlds_gdf = pd.concat(worlds)
    bounds_gdf = pd.concat(bounds)
    lines_gdf = pd.concat(lines)
    worlds_gdf = worlds_gdf.assign(color="#00BB00")
    bounds_gdf = bounds_gdf.assign(color="#000088")
    lines_gdf = lines_gdf.assign(color="#FFFFFF")
    
    s = pd.concat([bounds_gdf, worlds_gdf, lines_gdf])        
    s.plot(color=s["color"])

    #plt.axis("off")
    plt.axis("tight")
    plt.axis("image")
    plt.savefig("output/world_partitions.png", bbox_inches="tight", pad_inches=0, dpi=400)
    return plt

if __name__ == '__main__':
    #draw_stretch_world("world/World_Map_Geometry_fixed2.shp").show()
    draw_stretch_box("world/World_Map_Geometry_fixed2.shp", 6, -3).show()
    



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
