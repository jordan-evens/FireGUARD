from __future__ import print_function
#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_N80W180.tar.gz'
#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_N80W005.tar.gz'
#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_N80E000.tar.gz'
#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_N80E175.tar.gz'


#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_N00W180.tar.gz'
#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_S05W180.tar.gz'
#~ url = r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_S55W180.tar.gz'

import os
import multiprocessing
import tarfile
import math

import rasterio
from rasterio.merge import merge
from rasterio.plot import show
import glob
import util
import logging

DATA_DIR = os.path.realpath('../data')
GIS = os.path.join(DATA_DIR, 'GIS')
OUT_DIR = os.path.join(DATA_DIR, 'extracted/earthenv')
INPUT = os.path.join(GIS, "input")
GIS_ELEVATION = os.path.join(INPUT, "elevation")
EARTHENV = os.path.join(GIS_ELEVATION, "EarthEnv.tif")
MASK = r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_{}{}.tar.gz'
DOWNLOAD_DIR = os.path.join(DATA_DIR, 'download/ftp', os.path.dirname(MASK.replace('http://', '')))

def define_bounds():
    import sys
    sys.path.append('../util')
    import common
    global RANGE_LATITUDE
    global RANGE_LONGITUDE
    MIN_LAT = int(common.BOUNDS['latitude']['min'] / 5) * 5
    if MIN_LAT < 0 and 0 != MIN_LAT  / 5:
        MIN_LAT -= 5
    MAX_LAT = math.ceil(common.BOUNDS['latitude']['max'] / 5) * 5
    if MAX_LAT < 85 and 0 != MAX_LAT / 5:
        MAX_LAT += 5
    RANGE_NORTH = map(lambda _: 'N{:02d}'.format(_),
                      [x for x in reversed([5 * x for x in list(xrange(17))]) if x >= MIN_LAT and x <= MAX_LAT])
    RANGE_SOUTH = map(lambda _: 'S{:02d}'.format(_),
                      [x for x in [(5 * (x + 1)) for x in list(xrange(11))] if -x >= MIN_LAT and -x <= MAX_LAT])
    MIN_LON = int(common.BOUNDS['longitude']['min'] / 5) * 5
    if MIN_LON < 0 and 0 != MIN_LON  / 5:
        MIN_LON -= 5
    MAX_LON = math.ceil(common.BOUNDS['longitude']['max'] / 5) * 5
    MAX_LON -= 5
    RANGE_WEST = map(lambda _: 'W{:03d}'.format(_),
                     [x for x in reversed([5 * (x + 1) for x in list(xrange(36))]) if -x >= MIN_LON and -x <= MAX_LON])
    RANGE_EAST = map(lambda _: 'E{:03d}'.format(_),
                     [x for x in [5 * x for x in list(xrange(36))] if x >= MIN_LON and x <= MAX_LON])
    RANGE_LATITUDE = RANGE_NORTH + RANGE_SOUTH
    RANGE_LONGITUDE = RANGE_WEST + RANGE_EAST


def to_download(url):
    return util.save_http(DOWNLOAD_DIR, url, ignore_existing=True)

if __name__ == '__main__':
    pool = multiprocessing.Pool(processes=4)
    urls = []
    define_bounds()
    for lat in RANGE_LATITUDE:
        for lon in RANGE_LONGITUDE:
            urls.append(MASK.format(lat, lon))
    print('Downloading...')
    files = pool.map(to_download, urls)
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)
    print('Extracting...')
    for f in files:
        print(f)
        tar = tarfile.open(f)
        tar.extractall(OUT_DIR)
        tar.close()
    if not os.path.exists(EARTHENV):
        if not os.path.exists(GIS_ELEVATION):
            os.makedirs(GIS_ELEVATION)
        print('Mosaicing...')
        search_criteria = "EarthEnv-DEM90_*.bil"
        q = os.path.join(OUT_DIR, search_criteria)
        dem_fps = glob.glob(q)
        src_files_to_mosaic = []
        for fp in dem_fps:
           #~ src = rasterio.open(fp)
           src_files_to_mosaic.append(fp)
        import sys
        sys.path.append(os.path.join(os.path.dirname(sys.executable), 'Scripts'))
        import gdal_merge as gm
        gm.main(['', '-co', 'COMPRESS=DEFLATE', '-co', 'BIGTIFF=YES', '-o', EARTHENV] + src_files_to_mosaic)
