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

MASK = r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/EarthEnv-DEM90_{}{}.tar.gz'
RANGE_NORTH = list(reversed(['N{:02d}'.format(5 * x) for x in list(xrange(17))]))
RANGE_SOUTH = ['S{:02d}'.format(5 * (x + 1)) for x in list(xrange(11))]
RANGE_WEST = list(reversed(['W{:03d}'.format(5 * (x + 1)) for x in list(xrange(36))]))
RANGE_EAST = ['E{:03d}'.format(5 * x) for x in list(xrange(36))]
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
        print url
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
            print f
            tar = tarfile.open(f)
            tar.extractall(OUT_DIR)
            tar.close()
    out_fp = 'EarthEnv.tif'
    search_criteria = "*.bil"
    q = os.path.join(OUT_DIR, search_criteria)
    dem_fps = glob.glob(q)
    src_files_to_mosaic = []
    for fp in dem_fps:
       src = rasterio.open(fp)
       src_files_to_mosaic.append(src)
    mosaic, out_trans = merge(src_files_to_mosaic)
    out_meta = src.meta.copy()
    out_meta.update({"driver": "GTiff",
                      "height": mosaic.shape[1],
                      "width": mosaic.shape[2],
                      "transform": out_trans,
                      #~ "crs": "+proj=utm +zone=35 +ellps=GRS80 +units=m +no_defs "
                      })
    with rasterio.open(out_fp, "w", **out_meta) as dest:
        dest.write(mosaic)


