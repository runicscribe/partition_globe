import numpy as np
from collections.abc import Iterable
from shapely.geometry import LineString, Point

lon_count = 16
base_step_stud = 6
base_step_deg = 360.0/lon_count
lon_offset = -177 # Use ... for earth
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

# step_coeficcients[LAT][EVEN/ODD][LON_MAX, LON_MIN, LAT_STEP]
step_coefficients = [
    [[1, 1, 1], [1, 1, 1]],
    [[1, 1, 1], [1, 2/3, 1]],
    [[1, 1/3, 1], [2/3, 2/3, 1]],
    [[1/3, 1/3, 2/3], [2/3, 1/3, 2/3]],
    [[1/3, 0, 5/6], [1/3, 0, 5/6]]
]
sc = 100 # pixels per stud

def get_segment(lon, lat):
    '''

    :param lon: Longitudinal index lon ∈ [0,15]
    :param lat: Latitudinal index lat ∈ [-4,4]
    :return:
    '''

    parity = lon % 2
    abs_lat = int(abs(lat))
    if lat != 0:
        hemisphere = lat / abs_lat
    else:
        hemisphere = 1
    coefficients = step_coefficients[abs_lat][parity]

    diam_lo_stud = base_step_stud * (coefficients[0] + step_coefficients[abs_lat][1 - parity][0]) * lon_count / 2
    diam_hi_stud = base_step_stud * (coefficients[1] + step_coefficients[abs_lat][1 - parity][1]) * lon_count / 2

    lon_lo_stud_to_deg = 360 / diam_lo_stud
    lon_hi_stud_to_deg = 360 / diam_hi_stud

    lon_step_lo_deg = lon_lo_stud_to_deg * coefficients[0] * base_step_stud
    lon_step_hi_deg = lon_hi_stud_to_deg * coefficients[1] * base_step_stud

    lat_min = -base_step_deg/2
    for i in range(0, abs_lat):
        lat_min = lat_min + base_step_deg*step_coefficients[i][parity][2]

    lat_max = lat_min + base_step_deg*coefficients[2]
    lat_mid = lat_min + base_step_deg*coefficients[2]/2
    lon_mid = lon*base_step_deg + lon_offset
    lon_min = lon_mid - lon_step_lo_deg / 2
    lon_max = lon_mid + lon_step_lo_deg / 2

    ll = [lon_mid - lon_step_lo_deg / 2, lat_min*hemisphere]
    lr = [lon_mid + lon_step_lo_deg / 2, lat_min*hemisphere]
    ul = [lon_mid - lon_step_hi_deg / 2, lat_max*hemisphere]
    ur = [lon_mid + lon_step_hi_deg / 2, lat_max*hemisphere]
    
    
    lo_stud_step = base_step_stud*coefficients[0]
    hi_stud_step = base_step_stud*coefficients[1]
    
    #TODO: This bit still isn't quite working
    # Project low width in lon to hi, convert to studs, ancor to square corner
    if hemisphere > 0:
        # Determine if we're a square or triangle to see if hight or low is wider 
        if hi_stud_step < lo_stud_step:
          print("Triangle, northern hemisphere")
          print(base_step_deg*coefficients[0]/lon_lo_stud_to_deg)
          offset = lo_stud_step - base_step_deg*coefficients[0]/lon_hi_stud_to_deg
          ll_stud = [0, sc*base_step_stud*coefficients[2]]
          lr_stud = [sc*base_step_stud*coefficients[0], sc*base_step_stud*coefficients[2]]
          ul_stud = [sc*offset/2, 0]
          ur_stud = [sc*(base_step_stud*coefficients[0] - offset/2), 0]
        else:
          print("Square, northern hemisphere")
          print(base_step_deg*coefficients[1]/lon_lo_stud_to_deg)
          offset = base_step_deg*coefficients[1]/lon_hi_stud_to_deg - lo_stud_step
          ll_stud = [sc*offset/2, sc*base_step_stud*coefficients[2]]
          lr_stud = [sc*(base_step_stud*coefficients[1] - offset/2), sc*base_step_stud*coefficients[2]]
          ul_stud = [0, 0]
          ur_stud = [sc*base_step_stud*coefficients[1], 0]

    elif hemisphere < 0:
        if hi_stud_step < lo_stud_step:
          print("Triangle, southern hemisphere")
          offset = lo_stud_step - base_step_deg*coefficients[0]/lon_hi_stud_to_deg
          ll_stud = [sc*offset/2, sc*base_step_stud*coefficients[2]]
          lr_stud = [sc*(base_step_stud*coefficients[0] - offset/2), sc*base_step_stud*coefficients[2]]
          ul_stud = [0, 0]
          ur_stud = [sc*base_step_stud*coefficients[0], 0]
        else:
          print("Square, southern hemisphere")
          offset = base_step_deg*coefficients[1]/lon_hi_stud_to_deg - lo_stud_step
          ll_stud = [0, sc*base_step_stud*coefficients[2]]
          lr_stud = [sc*base_step_stud*coefficients[1], sc*base_step_stud*coefficients[2]]
          ul_stud = [sc*offset/2, 0]
          ur_stud = [sc*(base_step_stud*coefficients[1]-offset/2), 0]
    else:
        ll_stud = [0, sc*base_step_stud*coefficients[2]]
        lr_stud = [sc*base_step_stud*coefficients[0], sc*base_step_stud*coefficients[2]]
        ul_stud = [0, 0]
        ur_stud = [sc*base_step_stud*coefficients[1], 0]

    grid = []
    #Latitude lines
    for i in range(-int(base_step_stud*coefficients[1]/2), int(base_step_stud*coefficients[1]/2)+1):
        grid.append(LineString([[lon_mid + i*lon_lo_stud_to_deg, lat_min*hemisphere], [lon_mid + i*lon_hi_stud_to_deg, lat_max*hemisphere]]))
    #Longitude lines (width is just max width, not scaled to box)
    for j in range(0, int(sc*base_step_stud*coefficients[2])):
        grid.append(LineString([[lon_mid - base_step_deg, (lat_min + j*base_step_deg/base_step_stud)*hemisphere], [lon_mid + base_step_deg, (lat_min + j*base_step_deg/base_step_stud)*hemisphere]]))

    if hemisphere < 0:
      transform = create_stretch_transform(lon_mid, 1/(base_step_stud*lon_hi_stud_to_deg), 1-lon_lo_stud_to_deg/lon_hi_stud_to_deg, hemisphere*lat_max,  1/(lat_max-lat_min), coefficients[2])
    else:
      #.42
      print("step lo {} step hi {} stud lo {} stud hi {}".format(lon_step_lo_deg, lon_step_hi_deg,lon_lo_stud_to_deg,lon_hi_stud_to_deg))
      transform = create_stretch_transform(lon_mid, 1/(base_step_stud*lon_lo_stud_to_deg), lon_lo_stud_to_deg/lon_hi_stud_to_deg-1, lat_min, 1/(lat_max-lat_min), coefficients[2])
      
    #if hemisphere < 0:
    #  transform = create_stretch_transform(lon_mid, lon_step_hi_deg/(lon_step_lo_deg*lon_step_lo_deg), hemisphere*(lon_step_hi_deg/lon_step_lo_deg-1), hemisphere, hemisphere*lat_max,  1/(lat_max-lat_min))
    #else:
    #  transform = create_stretch_transform(lon_mid, 1/(lon_step_lo_deg), lon_step_hi_deg/lon_step_lo_deg-1, hemisphere, lat_min, 1/(lat_max-lat_min))

    return LineString([ll, lr, ur, ul, ll]), grid, [ul_stud, ur_stud, ll_stud, lr_stud], transform



def get_transform(lon, lat):
    '''

    :param lon: Longitudinal index lon ∈ [0,15]
    :param lat: Latitudinal index lat ∈ [-4,4]
    :return:
    '''

    parity = lon % 2
    abs_lat = int(abs(lat))
    if lat != 0:
        hemisphere = lat / abs_lat
    else:
        hemisphere = 1
    coefficients = step_coefficients[abs_lat][parity]

    lat_step_stud = coefficients[2]*base_step_stud
    lat_step_deg = coefficients[2]*base_step_deg

    #To get step, take avg of even and odd
    lon_step_max_avg_stud = base_step_stud * (coefficients[0] + step_coefficients[abs_lat][1 - parity][0]) / 2
    lon_step_min_avg_stud = base_step_stud * (coefficients[1] + step_coefficients[abs_lat][1 - parity][1]) / 2

    lon_max_stud_to_deg = base_step_deg / lon_step_max_avg_stud
    lon_min_stud_to_deg = base_step_deg / lon_step_min_avg_stud
    lat_stud_to_deg = base_step_deg/base_step_stud
    square_stud = base_step_stud * coefficients[0]

    #TODO: Expand to encompass full square...
    lon_step_max_deg = lon_max_stud_to_deg*square_stud
    lon_step_min_deg = lon_min_stud_to_deg*square_stud

    lat_min = -base_step_deg/2
    for i in range(0, abs_lat):
        lat_min = lat_min + base_step_deg*step_coefficients[i][parity][2]

    lat_max = lat_min + base_step_deg*coefficients[2]
    lat_mid = lat_min + base_step_deg*coefficients[2]/2
    lon_mid = lon*base_step_deg
    lon_min = lon_mid - lon_step_max_deg/2
    lon_max = lon_mid + lon_step_max_deg/2
    deg_bbox = [lon_min, lon_max, lat_min, lat_max]

    ##TODO: matrix transform, stud_bbox
    # See also:
    #  - https://stackoverflow.com/questions/51691482/how-to-create-a-2d-perspective-transform-matrix-from-individual-components
    #  - https://docs.opencv.org/3.4.0/da/d6e/tutorial_py_geometric_transformations.html

    # Note: May be transposed, because reference suggests off-axis are correct params
    # First test against basic polygon: Polygon([(bbox[0], bbox[2]), (bbox[1], bbox[2]), (bbox[1], bbox[3]), (bbox[0], bbox[3]), (bbox[0], bbox[2])])

    #affine
    #transform = [lon_max_stud_to_deg, 0, -lon_mid, 0, lat_stud_to_deg, -lat_mid, 0, (lon_step_max_avg_stud/lon_step_min_avg_stud), 1]
    #TODO: Figure out translate first
    transform = [22.5/lon_max_stud_to_deg, 0, -lon_mid/lon_min_stud_to_deg, 0, lat_min/lat_stud_to_deg, -lat_min/lat_stud_to_deg, 0, lon_step_max_avg_stud/lon_step_min_avg_stud, 1]


    # TODO: Return transform, bbox, overlay poly
    return transform, deg_bbox, None


    # Example (via GIMP transform test, might not be best reference):
    #    __
    #   /  \
    #  /____\
    #  0.5, -0.3, 200
    #    0,  0.5, 0.5
    #    0,    0,   1
    #
    #   cx,   sx,  tx | x
    #   sy,   cy,  ty | y
    #   lx,   ly,   1 | 1
    #
def create_matrix_transform(matrix):
    print(matrix)
    cx, sx, tx, sy, cy, ty, lx, ly, tz = matrix

    def matrix_transform(x, y, z=None):
        if isinstance(x, Iterable):
            raise TypeError
        xp = cx * x + sx * y + tx
        yp = sy * x + cy * y + ty
        zp = lx * x + ly * y + tz

        return tuple(filter(lambda a: a is not None, [xp/zp, yp/zp]))

    return matrix_transform

#TODO: Try this again: Linear scale of x coordinate relative to x_mid based on ratio of y to ymin/stud_to_deg + ymax/stud_to_deg. y is unchanged
# Apply to geoms after clipping.
def create_stretch_transform(x_mid, x_scale, x_ratio, y_low, y_scale, y_coeff):
    print("X: off {} scale {} rat {} | Y: off {} scale {}".format(x_mid, x_scale, x_ratio, y_low, y_scale))

    def stretch_transform(x, y, z=None):
        if isinstance(x, Iterable):
            raise TypeError
        #scale y to [0:1]
        yp = (y - y_low)*y_scale
        xp = (x - x_mid)*x_scale*(1 + (yp*x_ratio))


        return tuple(filter(lambda a: a is not None, [xp, yp*y_coeff]))

    return stretch_transform