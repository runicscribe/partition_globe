
from partition import get_segment
from shapely.ops import transform
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
from collections.abc import Iterable

# Tool for converting a regular world map in lon/lat coordinates into quadrants compatible with the layout of
# LEGO #21332 "The Globe", to assist in the creation of custom maps

green = "#108440"
dk_blue = "#072a64"

def draw_world(world_shp):
    """
    Draw all quadrants in WGS84
    :param world_shp: Name of the shapefile to render within quadrants
    :return:
    """

    grids = []
    outlines = []
    for lon in range(0, 16):
        for lat in range(-3, 4):
            border, grid, tf = get_segment(lon, lat)
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
    """
    Draw a single quadrant in WGS84
    :param world_shp: Name of the shapefile to render within quadrants
    :param x: X-coordinate of quadrant x E [0,15]
    :param y: Y-coordinate of quadrant y E [-3,3]
    :return:
    """
    border, grid, tf = get_segment(x, y)
    grids = []
    for line in grid:
        grids.append({'color': "#FFFFFF", 'geometry': line})

    bounds = gpd.GeoDataFrame([{'color': dk_blue, 'geometry': border.convex_hull}], geometry='geometry', crs=None)
    lines = gpd.GeoDataFrame(grids, geometry='geometry', crs=None)
    lines.geometry = lines.buffer(0.1).clip(bounds)
    
    lines = lines.assign(color="#FFFFFF")
    world_gdf = gpd.read_file(world_shp).clip(bounds)
    world_gdf['color'] = green

    s = pd.concat([bounds, world_gdf, lines])
    s.plot(color=s["color"])

    plt.axis("off")
    plt.axis("tight")
    plt.axis("image")
    plt.savefig("output/grid_{}_{}.png".format(x, y), bbox_inches="tight", pad_inches=0)
    return plt


def build_stretch_box(world_shp, x, y):
    """
    Warped a single quadrant to square coordinates
    :param world_shp: Name of the shapefile to render within quadrants
    :param x: X-coordinate of quadrant x E [0,15]
    :param y: Y-coordinate of quadrant y E [-3,3]
    :return: [bounds_tf, lines_tf, world_tf] bounds, gridlines, and geometry dataframes, warped to square
    """
    border, grid, tf = get_segment(x, y)

    # Shapely transform to shift by x, y-0.5, to layout segments around world
    def shift_transform(i, j, k=None):
        if isinstance(i, Iterable):
            raise TypeError
        # scale y to [0:1]
        xp = i+x
        yp = j+y-0.5
        # Last segment is 4 tall instead of 6, so shift up by 1/3
        if y == -3:
            yp = yp + 1/3

        return tuple(filter(lambda a: a is not None, [xp, yp]))

    grids = []
    grids_tf = []
    for line in grid:
        grids.append({'color': "#FFFFFF", 'geometry': line})
        grids_tf.append({'color': "#FFFFFF", 'geometry': transform(shift_transform, transform(tf, line))})
    
    bounds = gpd.GeoDataFrame([{'color': dk_blue, 'geometry': border.convex_hull}], geometry='geometry', crs="EPSG:4326")
    lines = gpd.GeoDataFrame(grids, geometry='geometry')

    world_gdf = gpd.read_file(world_shp).clip(bounds)
    
    bounds_tf = gpd.GeoDataFrame([{'color': dk_blue, 'geometry': transform(shift_transform, transform(tf, border.convex_hull))}], geometry='geometry', crs=None)
    lines_tf = gpd.GeoDataFrame(grids_tf, geometry='geometry', crs=None)
    lines_tf.geometry = lines_tf.buffer(0.01).clip(bounds_tf)
    lines_tf = lines_tf.assign(color="#FFFFFF")
    
    if len(world_gdf.index) > 0:
        world_geom = world_gdf.dissolve().geometry.item()  # [list(world_gdf.geometry.exterior.iloc[row_id].coords) for row_id in range(world_gdf.shape[0])]
        world_tf = gpd.GeoDataFrame([{'color': green, 'geometry': transform(shift_transform, transform(tf, world_geom))}], geometry='geometry', crs=None)
        return [bounds_tf, lines_tf, world_tf]
    else:
        return [bounds_tf, lines_tf, None]


def draw_stretch_box(world_shp, x, y):
    """
    Draw a single quadrant, warped to square
    :param world_shp: Name of the shapefile to render within quadrants
    :param x: X-coordinate of quadrant x E [0,15]
    :param y: Y-coordinate of quadrant y E [-3,3]
    :return: The plot object the quadrant is drawn to
    """
    bounds, lines, world = build_stretch_box(world_shp, x, y)
    if world is not None:
        s = pd.concat([bounds, lines])
    else:
        s = pd.concat([bounds, lines, world])

    s.plot(color=s["color"])

    plt.axis("off")
    plt.axis("tight")
    plt.axis("image")
    plt.savefig("output/block_{}_{}.png".format(x, y), bbox_inches="tight", pad_inches=0)
    return plt


def draw_stretch_world(world_shp):
    """
    Draw all quadrants, warped to square

    :param world_shp: Name of the shapefile to render within quadrants
    :return: The plot object the quadrants are drawn to
    """
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
    worlds_gdf = worlds_gdf.assign(color=green)
    bounds_gdf = bounds_gdf.assign(color=dk_blue)
    lines_gdf = lines_gdf.assign(color="#FFFFFF")
    
    s = pd.concat([bounds_gdf, worlds_gdf, lines_gdf])        
    s.plot(color=s["color"])

    plt.axis("off")
    plt.axis("tight")
    plt.axis("image")
    plt.savefig("output/world_partitions.png", bbox_inches="tight", pad_inches=0, dpi=400)
    return plt


if __name__ == '__main__':
    draw_stretch_world("world/World_Map_Geometry_fixed2.shp").show()
    # draw_stretch_box("world/World_Map_Geometry_fixed2.shp", 0, -1).show()
