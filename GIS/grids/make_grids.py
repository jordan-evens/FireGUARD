import gc
#import shapefile
import rasterio
from rasterio.plot import show
from rasterio.plot import show_hist
from rasterio.mask import mask
from shapely.geometry import box
import geopandas as gpd
from fiona.crs import from_epsg
import pycrs
import gdal
import os
import fiona
import rasterio.mask
import rasterio.rio
import osr
from pyproj import Proj
import numpy as np
import math
import pandas as pd
import gdalconst

from Settings import Settings

settings = Settings()

CELL_SIZE = 100
DATA_DIR = os.path.realpath('/FireGUARD/data')
EXTRACTED_DIR = os.path.join(DATA_DIR, 'extracted')
DOWNLOAD_DIR = os.path.join(DATA_DIR, 'download')
GENERATED_DIR = os.path.join(DATA_DIR, 'generated')
DIR = os.path.join(GENERATED_DIR, 'grid')
TMP = os.path.realpath('/FireGUARD/data/tmp')
CREATION_OPTIONS = ['TILED=YES', 'BLOCKXSIZE=256', 'BLOCKYSIZE=256', 'COMPRESS=LZW']
EARTHENV = os.path.join(GENERATED_DIR, 'EarthEnv.tif')

def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]

ZONE_MIN = 15 + (settings.longitude_min + 93.0) / 6.0
if int(ZONE_MIN) + 0.5 > ZONE_MIN:
    ZONE_MIN = int(ZONE_MIN)
else:
    ZONE_MIN = int(ZONE_MIN) + 0.5
ZONE_MAX = 15 + (settings.longitude_max + 93.0) / 6.0
if round(ZONE_MAX, 0) < ZONE_MAX:
    ZONE_MAX = int(ZONE_MAX) + 0.5
else:
    ZONE_MAX = round(ZONE_MAX, 0)
if not os.path.exists(DIR):
    os.makedirs(DIR)
if not os.path.exists(TMP):
    os.makedirs(TMP)

def clip_zone(fp, prefix, zone):
    out_tif = os.path.join(DIR, prefix + '_{}'.format(zone).replace('.', '_')) + '.tif'
    if os.path.exists(out_tif):
        return out_tif
    print(out_tif)
    meridian = (zone - 15.0) * 6.0 - 93.0
    wkt = 'PROJCS["NAD_1983_UTM_Zone_{}N",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",{}],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]'.format(zone, meridian)
    proj_srs = osr.SpatialReference(wkt=wkt)
    toProj = Proj(proj_srs.ExportToProj4())
    lat = (meridian, meridian)
    lon = (settings.latitude_min, settings.latitude_max)
    df = pd.DataFrame(np.c_[lat, lon], columns=['Longitude', 'Latitude'])
    x, y = toProj(df['Longitude'].values, df['Latitude'].values)
    MIN_EASTING = 300000
    MAX_EASTING = 700000
    MIN_NORTHING = int(y[0] / 100000) * 100000
    MAX_NORTHING = (int(y[1] / 100000) + 1) * 100000
    ds = gdal.Open(fp)
    out_image = None
    out_transform = None
    data = rasterio.open(fp)
    srcWkt = data.crs.wkt
    data.close()
    srcSRS = osr.SpatialReference()
    srcSRS.ImportFromWkt(data.crs.wkt)
    dstSRS = osr.SpatialReference()
    dstSRS.ImportFromWkt(wkt)
    rb = ds.GetRasterBand(1)
    no_data = rb.GetNoDataValue()
    rb = None
    ds = gdal.Warp(out_tif,
                   ds,
                   format='GTiff',
                   outputBounds=[MIN_EASTING, MIN_NORTHING, MAX_EASTING, MAX_NORTHING],
                   creationOptions=CREATION_OPTIONS,
                   xRes=CELL_SIZE,
                   yRes=CELL_SIZE,
                   srcSRS=srcWkt,
                   dstSRS=wkt)
    ds = None
    # HACK: make sure nodata value is set because C code expects it even if nothing is nodata
    ds = gdal.Open(out_tif, 1)
    rb = ds.GetRasterBand(1)
    # HACK: for some reason no_data is a double??
    if no_data is None:
        rb.SetNoDataValue(int(-math.pow(2, 15) - 1))
    rb = None
    ds = None
    gc.collect()
    return out_tif

zone = ZONE_MIN
while zone <= ZONE_MAX:
    dem = clip_zone(EARTHENV, 'dem', zone)
    slope = dem.replace('dem_', 'slope_')
    if not os.path.exists(slope):
        print(slope)
        tmp_slope = slope.replace(DIR, TMP)
        gdal.DEMProcessing(tmp_slope, dem, 'slope', creationOptions=CREATION_OPTIONS)
        gdal.Translate(slope, tmp_slope, outputType=gdalconst.GDT_UInt16, creationOptions=CREATION_OPTIONS)
    aspect = dem.replace('dem_', 'aspect_')
    if not os.path.exists(aspect):
        print(aspect)
        tmp_aspect = aspect.replace(DIR, TMP)
        gdal.DEMProcessing(tmp_aspect, dem, 'aspect', creationOptions=CREATION_OPTIONS)
        gdal.Translate(aspect, tmp_aspect, outputType=gdalconst.GDT_UInt16, creationOptions=CREATION_OPTIONS)
    fbp = clip_zone(os.path.join(EXTRACTED_DIR, r'fbp\fuel_layer\FBP_FuelLayer.tif'), 'fuel', zone)
    zone += 0.5
