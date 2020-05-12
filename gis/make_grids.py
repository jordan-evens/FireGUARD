import shapefile
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

from Settings import Settings

settings = Settings()

DIR = 'grid'

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
    os.mkdir(DIR)

zone = ZONE_MIN
while zone <= ZONE_MAX:
    zone_fmt = '{}'.format(zone).replace('.', '_')
    shp_base = 'utm_{}'.format(zone_fmt)
    shp = os.path.join(DIR, shp_base)
    w = shapefile.Writer(shp, shapeType=5)
    w.field('ZONE', 'F')
    w.poly([[[300000, 0], [300000, 9300000], [700000, 9300000], [700000, 0]]])
    w.record(zone)
    w.close()
    with open(shp + '.prj', "wb") as prj:
        #~ epsg = 'PROJCS["WGS_1984_UTM_Zone_15N",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-93],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["Meter",1]]'
        epsg = 'PROJCS["NAD_1983_UTM_Zone_{}N",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",{}],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]'.format(zone, (zone - 15.0) * 6.0 - 93.0)
        prj.write(epsg)
        prj.close()
    #~ import fiona
    #~ import rasterio
    #~ import rasterio.mask
    #~ with fiona.open(shp + '.shp', "r") as shapefile:
        #~ shapes = [feature["geometry"] for feature in shapefile]
    #~ with rasterio.open("EarthEnv.tif") as src:
        #~ out_image, out_transform = rasterio.mask.mask(src, shapes, crop=True)
        #~ out_meta = src.meta
    fp = 'EarthEnv.tif'
    out_tif = shp.replace('utm_', 'dem_') + '.tif'
    data = rasterio.open(fp)
    geo = gpd.read_file(shp + '.shp')
    geo = geo.to_crs(crs=data.crs.data)
    proj = shp + '_proj.shp'
    geo.to_file(proj)
    data.close()
    coords = getFeatures(geo)
    c_fixed = coords[0]['coordinates'][0]
    for i in xrange(len(c_fixed)):
        c_fixed[i] = [min(max(settings.longitude_min, c_fixed[i][0]), settings.longitude_max),
                      min(max(settings.latitude_min, c_fixed[i][1]), settings.latitude_max)]
    min_lat = settings.latitude_max
    max_lat = settings.latitude_min
    min_lon = settings.longitude_max
    max_lon = settings.longitude_min
    for c in c_fixed:
        min_lon = min(min_lon, c[0])
        max_lon = max(max_lon, c[0])
        min_lat = min(min_lat, c[1])
        max_lat = max(max_lat, c[1])
    #~ out_img, out_transform = mask(data, shapes=coords, all_touched=True, crop=True)
    out_meta = data.meta.copy()
    epsg_code = int(data.crs.data['init'][5:])
    print(epsg_code)
    #~ print('Cropping raster')
    import rasterio.rio
    #~ ds = gdal.Open(fp)
    # this is very wrong because the lat/lon bounds don't work after projecting
    #~ gdal.Translate(out_tif,
                   #~ ds,
                   #~ projWin=[min_lon, max_lat, max_lon, min_lat])
    #~ ds = None
    #~ ds = gdal.Warp(out_tif,
                   #~ ds,
                   #~ format='GTiff',
                   #~ cutlineDSName=proj,
                   #~ cutlineSQL='SELECT * FROM ' + shp_base + '_proj',
                   #~ cutlineLayer=shp_base + '_proj',
                   #~ # outputBounds=[min_lon, min_lat, max_lon, max_lat],
                   #~ multithread=True,
                   #~ cropToCutline=True)
    #~ ds = gdal.Warp(out_tif,
                   #~ ds,
                   #~ format='GTiff',
                   #~ outputBounds=[min_lon, min_lat, max_lon, max_lat],
                   #~ multithread=True)
    ds = None
    zone += 0.5
