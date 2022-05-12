import numpy as np
from collections.abc import Iterable
from shapely.geometry import LineString, Point

# Utilities for partitioning a lat/lon globe into semi-regular partitions matching each plate on the surface of
# LEGO #21332 "The Globe" - 16 segments along the lines of longitude, 7 segments along the lines of lattitude

lon_count = 16
base_step_stud = 6
base_step_deg = 360.0/lon_count
lon_offset = -177  # Use -168 for earth
lat_count = 4


#  LON,LAT   Even    Odd
#  0,4
#  0,3
#  0,2
#  0,1
#  0,0       22.5,22.5
#  0,-1
#  0,-2
#  0,-3
#  0,-4

# Cooeficients describing the shape of each quadrant
# First index is abs(lat) where lat is the vertical quadrant E [-3,3] (Since the shapes of northern and southern quadrants are mirrored)
# Second index is the modulus of the lon E [0, 16] (since every other longitudinal quadrant is shaped the same)
# Items are width of quadrant base, width of the quadrant top, and height of the quadrant (1 = 6 studs)
#
# step_coeficcients[LAT][EVEN/ODD][LON_MAX, LON_MIN, LAT_STEP]
step_coefficients = [
    [[1, 1, 1], [1, 1, 1]],
    [[1, 1, 1], [1, 2/3, 1]],
    [[1, 1/3, 1], [2/3, 2/3, 1]],
    [[1/3, 1/3, 2/3], [2/3, 1/3, 2/3]],
    [[1/3, 0, 5/6], [1/3, 0, 5/6]]
]
sc = 100  # pixels per stud [deprecated]


def get_segment(lon, lat):
    '''

    :param lon: Longitudinal index lon ∈ [0,15]
    :param lat: Latitudinal index lat ∈ [-4,4]
    :return:
    '''

    # Extract cooeficient indices from lon/lat
    parity = lon % 2
    abs_lat = int(abs(lat))
    if lat != 0:
        hemisphere = lat / abs_lat
    else:
        hemisphere = 1
    coefficients = step_coefficients[abs_lat][parity]

    # Calculate size of quadrant in studs, from cooeficients
    diam_lo_stud = base_step_stud * (coefficients[0] + step_coefficients[abs_lat][1 - parity][0]) * lon_count / 2
    diam_hi_stud = base_step_stud * (coefficients[1] + step_coefficients[abs_lat][1 - parity][1]) * lon_count / 2

    # Calculate conversion factor between studs and degrees for top and bottom of quadrant
    lon_lo_stud_to_deg = 360 / diam_lo_stud
    lon_hi_stud_to_deg = 360 / diam_hi_stud

    # Calculate width of quadrant in degrees
    lon_step_lo_deg = lon_lo_stud_to_deg * coefficients[0] * base_step_stud
    lon_step_hi_deg = lon_hi_stud_to_deg * coefficients[1] * base_step_stud

    # Calculate lower latitude of the quadrant
    lat_min = -base_step_deg/2
    for i in range(0, abs_lat):
        lat_min = lat_min + base_step_deg*step_coefficients[i][parity][2]

    # Calculate the other lat/lon coordinates of the quadrant
    lat_max = lat_min + base_step_deg*coefficients[2]
    lat_mid = lat_min + base_step_deg*coefficients[2]/2
    lon_mid = lon*base_step_deg + lon_offset
    lon_min = lon_mid - lon_step_lo_deg / 2
    lon_max = lon_mid + lon_step_lo_deg / 2

    ll = [lon_mid - lon_step_lo_deg / 2, lat_min*hemisphere]
    lr = [lon_mid + lon_step_lo_deg / 2, lat_min*hemisphere]
    ul = [lon_mid - lon_step_hi_deg / 2, lat_max*hemisphere]
    ur = [lon_mid + lon_step_hi_deg / 2, lat_max*hemisphere]

    grid = []
    # Construct Latitude lines
    for i in range(-int(base_step_stud*coefficients[1]/2), int(base_step_stud*coefficients[1]/2)+1):
        grid.append(LineString([[lon_mid + i*lon_lo_stud_to_deg, lat_min*hemisphere], [lon_mid + i*lon_hi_stud_to_deg, lat_max*hemisphere]]))
    # Construct Longitude lines (width is just max width, not scaled to box)
    for j in range(0, int(sc*base_step_stud*coefficients[2])):
        grid.append(LineString([[lon_mid - base_step_deg, (lat_min + j*base_step_deg/base_step_stud)*hemisphere], [lon_mid + base_step_deg, (lat_min + j*base_step_deg/base_step_stud)*hemisphere]]))

    # Create a shapely transform for warping Lon/Lat to studs
    if hemisphere < 0:
        transform = create_stretch_transform(
          lon_mid,                                  # x_mid
          1/(base_step_stud*lon_hi_stud_to_deg),    # x_scale
          lon_hi_stud_to_deg/lon_lo_stud_to_deg-1,  # x_ratio
          hemisphere*lat_max,                       # y_low
          1/(lat_max-lat_min),                      # y_scale
          coefficients[2])                          # y_coeff
    else:
        transform = create_stretch_transform(
          lon_mid,                                  # x_mid
          1/(base_step_stud*lon_lo_stud_to_deg),    # x_scale
          lon_lo_stud_to_deg/lon_hi_stud_to_deg-1,  # x_ratio
          lat_min,                                  # y_low
          1/(lat_max-lat_min),                      # y_scale
          coefficients[2])                          # y_coeff

    return LineString([ll, lr, ur, ul, ll]), grid, transform


def create_stretch_transform(x_mid, x_scale, x_ratio, y_low, y_scale, y_coeff):
    """
    Shapely WGS84 to stud transform
    Linear scale of x coordinate relative to x_mid based on ratio of y to ymin/stud_to_deg + ymax/stud_to_deg. y is unchanged
    Should be applyied to geoms after clipping.

    :param x_mid: X translation
    :param x_scale: Base x scale
    :param x_ratio: Additional X scale relative to y
    :param y_low: Y translation
    :param y_scale: Y scale to y E [0:1]
    :param y_coeff: Additional Y scale to match LAT_STEP coefficents of quadrant (applied after x scaling)
    :return:
    """
    #print("X: off {} scale {} rat {} | Y: off {} scale {}".format(x_mid, x_scale, x_ratio, y_low, y_scale))

    def stretch_transform(x, y, z=None):
        if isinstance(x, Iterable):
            raise TypeError
        # scale y to [0:1]
        yp = (y - y_low)*y_scale
        # scale x to [-0.5,0.5] at base (y=0), then scale according to y scale
        xp = (x - x_mid)*x_scale*(1 + (yp*x_ratio))

        return tuple(filter(lambda a: a is not None, [xp, yp*y_coeff]))

    return stretch_transform
