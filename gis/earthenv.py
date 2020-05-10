from __future__ import print_function
#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_N80W180.tar.gz'
#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_N80W005.tar.gz'
#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_N80E000.tar.gz'
#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_N80E175.tar.gz'


#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_N00W180.tar.gz'
#~ r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_S05W180.tar.gz'
#~ url = r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_S55W180.tar.gz'

import urllib2
import os
import multiprocessing
import tarfile

import rasterio
from rasterio.merge import merge
from rasterio.plot import show
import glob
import georasters

from Settings import Settings

settings = Settings()
MASK = r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_{}{}.tar.gz'
MIN_LAT = int(settings.latitude_min / 5) * 5
if MIN_LAT < 0 and 0 != MIN_LAT  / 5:
    MIN_LAT -= 5
MAX_LAT = int(settings.latitude_max / 5) * 5
RANGE_NORTH = map(lambda _: 'N{:02d}'.format(_),
                  [x for x in reversed([5 * x for x in list(xrange(17))]) if x >= MIN_LAT and x <= MAX_LAT])
RANGE_SOUTH = map(lambda _: 'S{:02d}'.format(_),
                  [x for x in [(5 * (x + 1)) for x in list(xrange(11))] if -x >= MIN_LAT and -x <= MAX_LAT])
MIN_LON = int(settings.longitude_min / 5) * 5
if MIN_LON < 0 and 0 != MIN_LON  / 5:
    MIN_LON -= 5
MAX_LON = int(settings.longitude_max / 5) * 5
MAX_LON -= 5
RANGE_WEST = map(lambda _: 'W{:03d}'.format(_),
                 [x for x in reversed([5 * (x + 1) for x in list(xrange(36))]) if -x >= MIN_LON and -x <= MAX_LON])
RANGE_EAST = map(lambda _: 'E{:03d}'.format(_),
                 [x for x in [5 * x for x in list(xrange(36))] if x >= MIN_LON and x <= MAX_LON])
RANGE_LATITUDE = RANGE_NORTH + RANGE_SOUTH 
RANGE_LONGITUDE = RANGE_WEST + RANGE_EAST
OUT_DIR = 'data'


def download(url, to_dir='.', to_file=None):
    if to_file is None:
        to_file = os.path.basename(url)
    if not os.path.exists(to_dir):
        os.mkdir(to_dir)
    to_file = os.path.join(to_dir, to_file)
    if not os.path.exists(to_file):
        print(url)
        filedata = urllib2.urlopen(url)
        datatowrite = filedata.read()
        with open(to_file, 'wb') as f:
            f.write(datatowrite)
    return to_file

def to_download(url):
    return download(url, 'download')

if __name__ == '__main__':
    pool = multiprocessing.Pool(processes=4)
    urls = []
    for lat in RANGE_LATITUDE:
        for lon in RANGE_LONGITUDE:
            urls.append(MASK.format(lat, lon))
    files = pool.map(to_download, urls)
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)
        for f in files:
            print(f)
            tar = tarfile.open(f)
            tar.extractall(OUT_DIR)
            tar.close()
    out_fp = 'EarthEnv.tif'
    if not os.path.exists(out_fp):
        search_criteria = "EarthEnv-DEM90_*.bil"
        q = os.path.join(OUT_DIR, search_criteria)
        dem_fps = glob.glob(q)
        src_files_to_mosaic = []
        for fp in dem_fps:
           #~ src = rasterio.open(fp)
           src_files_to_mosaic.append(fp)
        import sys
        sys.path.append(r'C:\Python27\ArcGIS10.3\Scripts')
        import gdal_merge as gm
        gm.main(['', '-co', 'COMPRESS=DEFLATE', '-o', out_fp] + src_files_to_mosaic)
