from __future__ import print_function
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
from osgeo import ogr

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
        no_data = int(-math.pow(2, 15) - 1)
        rb.SetNoDataValue(no_data)
    rb = None
    ds = None
    gc.collect()
    return out_tif

def clip_fuel(fp, prefix, zone):
    # fp = os.path.join(EXTRACTED_DIR, r'fbp\fuel_layer\FBP_FuelLayer.tif')
    # prefix = 'fuel'
    # zone = 15.0
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
        no_data = int(-math.pow(2, 15) - 1)
        rb.SetNoDataValue(no_data)
    print('Removing water')
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    vals = rb.ReadAsArray(0, 0, cols, rows)
    # get rid of water (102)
    vals[vals == 102] = no_data
    rb.WriteArray(vals, 0, 0)
    rb.FlushCache()
    rb = None
    ds = None
    gc.collect()
    gdb_driver = ogr.GetDriverByName("OpenFileGDB")
    # outdriver=ogr.GetDriverByName('MEMORY')
    outdriver=ogr.GetDriverByName('ESRI Shapefile')
    print('Adding water from polygons')
    # FIX: need to add USA water
    # FIX: check bounds for provinces and don't add if not near raster
    for prov in ['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT']:
        print('Adding {}'.format(prov))
        path_gdb = r'C:\FireGUARD\data\extracted\canvec\canvec_50K_{}_Hydro.gdb'.format(prov)
        gdb = gdb_driver.Open(path_gdb, 0)
        lakes = gdb.GetLayer('waterbody_2')
        lakes_ref = lakes.GetSpatialRef()
        ds = gdal.Open(out_tif, 1)
        transform = ds.GetGeoTransform()
        pixelWidth = transform[1]
        pixelHeight = transform[5]
        cols = ds.RasterXSize
        rows = ds.RasterYSize
        xLeft = transform[0]
        yTop = transform[3]
        xRight = xLeft+cols*pixelWidth
        yBottom = yTop+rows*pixelHeight
        raster_ref = osr.SpatialReference(wkt=ds.GetProjection())
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(xLeft, yTop)
        ring.AddPoint(xLeft, yBottom)
        ring.AddPoint(xRight, yBottom)
        ring.AddPoint(xRight, yTop)
        ring.AddPoint(xLeft, yTop)
        rasterGeometry = ogr.Geometry(ogr.wkbPolygon)
        rasterGeometry.AddGeometry(ring)
        rasterGeometry.AssignSpatialReference(raster_ref)
        coordTrans = osr.CoordinateTransformation(raster_ref, lakes_ref)
        rasterGeometry.Transform(coordTrans)
        e1 = rasterGeometry.GetEnvelope()
        e2 = lakes.GetExtent()
        r = ogr.Geometry(ogr.wkbLinearRing)
        r.AddPoint(e2[0], e2[3])
        r.AddPoint(e2[0], e2[2])
        r.AddPoint(e2[1], e2[2])
        r.AddPoint(e2[1], e2[3])
        r.AddPoint(e2[0], e2[3])
        vectorGeometry = ogr.Geometry(ogr.wkbPolygon)
        vectorGeometry.AddGeometry(r)
        vectorGeometry.AssignSpatialReference(lakes_ref)
        # FIX: just check full extent once and not every feature
        # intersects = False
        # for f in lakes:
            # vectorGeometry = f.GetGeometryRef()
            # intersects = rasterGeometry.Intersect(vectorGeometry)
            # if intersects:
                # break
        # just expecting RasterizeLayer to handle projection and everything
        # just do basic math for now
        # if (e1[0] >= e2[0] and e1[0] <= e2[1])
        # keep = []
        if vectorGeometry.Intersect(rasterGeometry):
            print('Province {} intersects zone'.format(prov))
            # source=outdriver.CreateDataSource('memData')
            raster_path = os.path.realpath('./raster.shp')
            # Remove output shapefile if it already exists
            if os.path.exists(raster_path):
                outdriver.DeleteDataSource(raster_path)
            # Create the output shapefile
            rasterSource = outdriver.CreateDataSource(raster_path)
            rasterLayer = rasterSource.CreateLayer('raster', lakes_ref, geom_type=ogr.wkbPolygon)
            featureDefn = rasterLayer.GetLayerDefn()
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(rasterGeometry)
            rasterLayer.CreateFeature(feature)
            feature = None
            tmp_path = os.path.realpath('./tmp.shp')
            if os.path.exists(tmp_path):
                outdriver.DeleteDataSource(tmp_path)
            source = outdriver.CreateDataSource(tmp_path)
            # tmpLayer = source.CreateLayer('FINAL', lakes_ref, geom_type=ogr.wkbMultiPolygon)
            tmpLayer = source.CreateLayer('tmp', lakes_ref, geom_type=ogr.wkbMultiPolygon)
            ogr.Layer.Clip(lakes, rasterLayer, tmpLayer)
            coordTrans = osr.CoordinateTransformation(lakes_ref, raster_ref)
            outputShapefile = os.path.realpath('./projected.shp')
            if os.path.exists(outputShapefile):
                outdriver.DeleteDataSource(outputShapefile)
            outDataSet = outdriver.CreateDataSource(outputShapefile)
            outLayer = outDataSet.CreateLayer("lakes", raster_ref, geom_type=ogr.wkbMultiPolygon)
            # add fields
            inLayerDefn = tmpLayer.GetLayerDefn()
            for i in range(0, inLayerDefn.GetFieldCount()):
                fieldDefn = inLayerDefn.GetFieldDefn(i)
                outLayer.CreateField(fieldDefn)
            # get the output layer's feature definition
            outLayerDefn = outLayer.GetLayerDefn()
            # loop through the input features
            inFeature = tmpLayer.GetNextFeature()
            while inFeature:
                # get the input geometry
                geom = inFeature.GetGeometryRef()
                # reproject the geometry
                geom.Transform(coordTrans)
                # create a new feature
                outFeature = ogr.Feature(outLayerDefn)
                # set the geometry and attribute
                outFeature.SetGeometry(geom)
                for i in range(0, outLayerDefn.GetFieldCount()):
                    outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
                # add the feature to the shapefile
                outLayer.CreateFeature(outFeature)
                # dereference the features and get the next input feature
                outFeature = None
                inFeature = tmpLayer.GetNextFeature()
            # check each feature
            # for f in lakes:
                # lakeGeometry = f.GetGeometryRef()
                # intersects = rasterGeometry.Intersect(lakeGeometry)
                # if intersects:
                    # keep.append(f)
            # shapes = ((geom,value) for geom, value in zip(keep, [102]*len(keep)))
            # burned = features.rasterize(shapes=keep, transform=transform)
            gdal.RasterizeLayer(ds, [1], outLayer, burn_values=[102])
            # Save and close the shapefiles
            inDataSet = None
            outDataSet = None
            rasterSource = None
            source = None
            # gdal.RasterizeLayer(ds, [1], lakes, burn_values=[102])
        ds = None
        lakes = None
        gdb = None
    # now need to fill in the nodata values that are left
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
    fbp = clip_fuel(os.path.join(EXTRACTED_DIR, r'fbp\fuel_layer\FBP_FuelLayer.tif'), 'fuel', zone)
    zone += 0.5
