# Partition Globe

Python Tool for converting a regular world map in lon/lat coordinates into quadrants compatible with the layout of
LEGO [#21332 "The Globe"](https://www.lego.com/en-ca/product/the-globe-21332), to assist in the creation of custom maps

Requires GeoPandas, and all its requirements, including GDAL.
Running this from a GIS Development platform such as Anaconda is recommended if you are not familiar
with installing GDAL

Source data must consist of a shapefile in EPSG:4326

See the [img](./img) dir for example output.

## Usage

Edit the `__main__` section at the bottom of main.py to point to the shapefile you are using, then run the main.py 
script with python.
A matplotlib window will show a preview of the result, which will also be saved in `./output/world_partitions.png`

To change the color scheme of the result, edit the values of the `green` and `dk_blue` variables at the top of main.py.

## Installation

### Prerequisites

Requires Python 3

### Installation

```
pip install -r requirements.txt
```

### Windows

One of the dependencies for this project (geopandas) requires GDAL, which can be a little tricky to install on Windows. 
Before running the install command above, follow these steps:

Download the [gdal](https://www.lfd.uci.edu/~gohlke/pythonlibs/#_gdal), 
[fiona](https://www.lfd.uci.edu/~gohlke/pythonlibs/#_fiona), and 
[pygeos](https://www.lfd.uci.edu/~gohlke/pythonlibs/#_pygeos) wheels for your Python version and install each of them 
with:

```
python -m pip install path\to\wheel\file.whl
```

Download and install the [MS C++ build tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and restart 
your computer.

Then run `pip install -r requirements.txt` as above.