from __future__ import print_function
import gc
#import shapefile
import rasterio
from rasterio.merge import merge
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
import osgeo
import subprocess

from Settings import Settings

##########################
# https://stackoverflow.com/questions/3662361/fill-in-missing-values-with-nearest-neighbour-in-python-numpy-masked-arrays

from scipy import ndimage as nd

import sys
SCRIPTS_DIR = os.path.join(os.path.dirname(sys.executable), 'Scripts')
sys.path.append(SCRIPTS_DIR)
import gdal_merge as gm

def fill(data, invalid=None):
    """
    Replace the value of invalid 'data' cells (indicated by 'invalid') 
    by the value of the nearest valid data cell

    Input:
        data:    numpy array of any dimension
        invalid: a binary array of same shape as 'data'. True cells set where data
                 value should be replaced.
                 If None (default), use: invalid  = np.isnan(data)

    Output: 
        Return a filled array. 
    """
    #import numpy as np
    #import scipy.ndimage as nd

    if invalid is None: invalid = np.isnan(data)

    ind = nd.distance_transform_edt(invalid, return_distances=False, return_indices=True)
    return data[tuple(ind)]
###########################


settings = Settings()

CELL_SIZE = 100
DATA_DIR = os.path.realpath('/FireGUARD/data')
EXTRACTED_DIR = os.path.join(DATA_DIR, 'extracted')
DOWNLOAD_DIR = os.path.join(DATA_DIR, 'download')
GENERATED_DIR = os.path.join(DATA_DIR, 'generated')
INTERMEDIATE_DIR = os.path.join(DATA_DIR, 'intermediate')
DIR = os.path.join(GENERATED_DIR, 'grid')
TILED_DIR = os.path.join(GENERATED_DIR, 'tiled')
TMP = os.path.realpath('/FireGUARD/data/tmp')
CREATION_OPTIONS = ['TILED=YES', 'BLOCKXSIZE=256', 'BLOCKYSIZE=256', 'COMPRESS=LZW']
EARTHENV = os.path.join(DATA_DIR, 'GIS/input/elevation/EarthEnv.tif')
FUEL_RASTER = os.path.join(EXTRACTED_DIR, r'fbp\fuel_layer\FBP_FuelLayer.tif')

INT_FUEL = os.path.join(INTERMEDIATE_DIR, 'fuel')
DRIVER_SHP = ogr.GetDriverByName('ESRI Shapefile')
DRIVER_TIF = gdal.GetDriverByName('GTiff')
DRIVER_GDB = ogr.GetDriverByName("OpenFileGDB")

def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]

ZONE_MIN = 15 + (settings.longitude_min + 93.0) / 6.0
if int(ZONE_MIN) + 0.5 > ZONE_MIN:
    ZONE_MIN = float(int(ZONE_MIN))
else:
    ZONE_MIN = int(ZONE_MIN) + 0.5
ZONE_MAX = 15 + (settings.longitude_max + 93.0) / 6.0
if round(ZONE_MAX, 0) < ZONE_MAX:
    ZONE_MAX = int(ZONE_MAX) + 0.5
else:
    ZONE_MAX = float(round(ZONE_MAX, 0))
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

def checkAddLakes(zone, cols, rows, for_what, path_gdb, layer):
    print('Adding {}'.format(for_what))
    INT_FUEL = os.path.join(INTERMEDIATE_DIR, 'fuel')
    polywater_tif = os.path.join(INT_FUEL, 'polywater_{}'.format(zone).replace('.', '_')) + '.tif'
    outputShapefile = os.path.join(INT_FUEL, 'projected_{}_{}'.format(for_what, zone).replace('.', '_') + '.shp')
    outputRaster = os.path.join(INT_FUEL, 'water_{}_{}'.format(for_what, zone).replace('.', '_') + '.tif')
    if not os.path.exists(outputShapefile):
        gdb = DRIVER_GDB.Open(path_gdb, 0)
        lakes = gdb.GetLayerByName(layer)
        lakes_ref = lakes.GetSpatialRef()
        ds = gdal.Open(polywater_tif, 1)
        transform = ds.GetGeoTransform()
        pixelWidth = transform[1]
        pixelHeight = transform[5]
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
        if vectorGeometry.Intersect(rasterGeometry):
            print('Intersects zone - clipping...')
            raster_path = os.path.join(INT_FUEL, 'raster_{}'.format(zone).replace('.', '_') + '.shp')
            # Remove output shapefile if it already exists
            if os.path.exists(raster_path):
                DRIVER_SHP.DeleteDataSource(raster_path)
            # Create the output shapefile
            rasterSource = DRIVER_SHP.CreateDataSource(raster_path)
            rasterLayer = rasterSource.CreateLayer('raster', lakes_ref, geom_type=ogr.wkbPolygon)
            featureDefn = rasterLayer.GetLayerDefn()
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(rasterGeometry)
            rasterLayer.CreateFeature(feature)
            feature = None
            tmp_path = os.path.join(INT_FUEL, 'bounds_{}'.format(zone).replace('.', '_') + '.shp')
            # delete for now but name nicely in case we want to reuse existing
            if os.path.exists(tmp_path):
                DRIVER_SHP.DeleteDataSource(tmp_path)
            source = DRIVER_SHP.CreateDataSource(tmp_path)
            # tmpLayer = source.CreateLayer('FINAL', lakes_ref, geom_type=ogr.wkbMultiPolygon)
            tmpLayer = source.CreateLayer('tmp', lakes_ref, geom_type=ogr.wkbMultiPolygon)
            ogr.Layer.Clip(lakes, rasterLayer, tmpLayer)
            coordTrans = osr.CoordinateTransformation(lakes_ref, raster_ref)
            print('Reprojecting...')
            # if os.path.exists(outputShapefile):
                # DRIVER_SHP.DeleteDataSource(outputShapefile)
            outDataSet = DRIVER_SHP.CreateDataSource(outputShapefile)
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
        outDataSet = None
        rasterSource = None
        ds = None
    # check again to see if we made it or had it already
    if os.path.exists(outputShapefile) and not os.path.exists(outputRaster):
        ds = gdal.Open(polywater_tif, 1)
        transform = ds.GetGeoTransform()
        proj = ds.GetProjection()
        ds = None
        outDataSet = DRIVER_SHP.Open(outputShapefile)
        outLayer = outDataSet.GetLayer()
        ds = DRIVER_TIF.Create(outputRaster, cols, rows, 1, gdal.GDT_UInt16)
        ds.SetGeoTransform(transform)
        ds.SetProjection(proj)
        #~ ds = gdal.Open(polywater_tif, osgeo.gdalconst.GA_Update)
        print('Rasterizing...')
        band = ds.GetRasterBand(1)
        band.SetNoDataValue(0)
        gdal.RasterizeLayer(ds, [1], outLayer, burn_values=[102], options=['ALL_TOUCHED=TRUE'])
        ds.FlushCache()
        # Save and close the shapefiles
        outDataSet = None
        band = None
        outLayer = None
        transform = None
        ds = None
        source = None
        proj = None
    lakes = None
    gdb = None
    gc.collect()
    if os.path.exists(outputRaster):
        return outputRaster
    return None

def check_base(fp, zone):
    base_tif = os.path.join(INT_FUEL, 'base_{}'.format(zone).replace('.', '_')) + '.tif'
    if not os.path.exists(base_tif):
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
        ds = gdal.Warp(base_tif,
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
        ds = gdal.Open(base_tif, 1)
        rb = ds.GetRasterBand(1)
        # HACK: for some reason no_data is a double??
        if no_data is None:
            no_data = int(-math.pow(2, 15) - 1)
            rb.SetNoDataValue(no_data)
            rb.FlushCache()
        rb = None
        ds = None
    ds = gdal.Open(base_tif, 1)
    rows = ds.RasterYSize
    cols = ds.RasterXSize
    rb = ds.GetRasterBand(1)
    no_data = rb.GetNoDataValue()
    rb = None
    ds = None
    return base_tif, cols, rows, no_data

def check_nowater(base_tif, zone, cols, rows, no_data):
    nowater_tif = os.path.join(INT_FUEL, 'nowater_{}'.format(zone).replace('.', '_')) + '.tif'
    if not os.path.exists(nowater_tif):
        tmp_tif = os.path.join(INT_FUEL, 'tmp_{}'.format(zone).replace('.', '_')) + '.tif'
        ds = gdal.Open(base_tif, 1)
        dst_ds = DRIVER_TIF.CreateCopy(tmp_tif, ds, 0, options=CREATION_OPTIONS)
        dst_ds = None
        ds = None
        ds = gdal.Open(tmp_tif, 1)
        print('Removing water')
        rb = ds.GetRasterBand(1)
        vals = rb.ReadAsArray(0, 0, cols, rows)
        # get rid of water (102)
        vals[vals == 102] = no_data
        rb.WriteArray(vals, 0, 0)
        rb.FlushCache()
        vals = None
        rb = None
        # want a copy of this before we add the water back in so we can fill from non-water
        dst_ds = DRIVER_TIF.CreateCopy(nowater_tif, ds, 0, options=CREATION_OPTIONS)
        dst_ds = None
        ds = None
        os.remove(tmp_tif)
        gc.collect()
    return nowater_tif

def check_filled(base_tif, nowater_tif, zone, cols, rows, no_data):
    filled_tif = os.path.join(INT_FUEL, 'filled_{}'.format(zone).replace('.', '_')) + '.tif'
    if not os.path.exists(filled_tif):
        # now fill in blanks with surrounding fuels
        print('Filling spaces')
        # only fill area of original raster
        ds = gdal.Open(base_tif, 1)
        rb = ds.GetRasterBand(1)
        vals = rb.ReadAsArray(0, 0, cols, rows)
        no_data = rb.GetNoDataValue()
        vals = None
        rb = None
        ds = None
        # get the raster with no water to start with
        ds_nowater = gdal.Open(nowater_tif, 1)
        rb_nowater = ds_nowater.GetRasterBand(1)
        vals_nowater = rb_nowater.ReadAsArray(0, 0, cols, rows)
        # need a 1 where we want to fill in the blanks, so make that cover all nodata cells
        fill_what = vals_nowater == no_data
        # fill the nodata values that had a value in the base but not when there's no water
        rb_nowater = None
        ds_nowater = None
        # close this for now because of memory issues
        vals_nowater = None
        mask = None
        gc.collect()
        # ind = nd.distance_transform_edt(input, return_distances=False, return_indices=True)
        sampling=None
        return_distances=False
        return_indices=True
        distances=None
        indices=None
        gc.collect()
        input = np.atleast_1d(np.where(fill_what, 1, 0).astype(np.int8))
        fill_what = None
        gc.collect()
        from scipy.ndimage import _nd_image
        # should be able to just use int16 for indices, but it must rely on it being int32 because it's wrong if it isn't
        tmp_np = os.path.join(INT_FUEL, 'tmp_{}'.format(zone).replace('.', '_')) + '.np'
        ft = np.memmap(tmp_np, dtype=np.int32, mode='w+', shape=(input.ndim,) + input.shape)
        _nd_image.euclidean_feature_transform(input, sampling, ft)
        ft.flush()
        input = None
        gc.collect()
        ds_nowater = gdal.Open(nowater_tif, 1)
        rb_nowater = ds_nowater.GetRasterBand(1)
        vals_nowater = rb_nowater.ReadAsArray(0, 0, cols, rows)
        filled = vals_nowater[tuple(ft)]
        vals_nowater = None
        rb_nowater = None
        ds_nowater = None
        ds = gdal.Open(base_tif, 1)
        dst_ds = DRIVER_TIF.CreateCopy(filled_tif, ds, 0, options=CREATION_OPTIONS)
        dst_ds = None
        ds = gdal.Open(filled_tif, 1)
        rb = ds.GetRasterBand(1)
        rb.WriteArray(filled, 0, 0)
        # rb.WriteArray(vals_nowater[tuple(ft)], 0, 0)
        rb.FlushCache()
        rb = None
        ds = None
        ft = None
        os.remove(tmp_np)
        gc.collect()
    return filled_tif

def check_merged(filled_tif, zone, cols, rows):
    polywater_tif = os.path.join(INT_FUEL, 'polywater_{}'.format(zone).replace('.', '_')) + '.tif'
    merged_tif = os.path.join(INT_FUEL, 'merged_{}'.format(zone).replace('.', '_')) + '.tif'
    # now the nodata values should all be filled, so apply the water from the polygons
    if not os.path.exists(merged_tif):
        ds_filled = gdal.Open(filled_tif, 1)
        dst_ds = DRIVER_TIF.CreateCopy(polywater_tif, ds_filled, 0, options=CREATION_OPTIONS)
        dst_ds = None
        ds_filled = None
        gc.collect()
        print('Adding water from polygons')
        water = [checkAddLakes(zone, cols, rows, 'USA_Lakes', r'C:\FireGUARD\data\extracted\nhd\NHD_H_National_GDB.gdb', r'NHDWaterbody')]
        water += [checkAddLakes(zone, cols, rows, 'USA_Other', r'C:\FireGUARD\data\extracted\nhd\NHD_H_National_GDB.gdb', r'NHDArea')]
        for prov in ['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT']:
            path_gdb = r'C:\FireGUARD\data\extracted\canvec\canvec_50K_{}_Hydro.gdb'.format(prov)
            water += [checkAddLakes(zone, cols, rows, prov, path_gdb, 'waterbody_2')]
        # should have a list of rasters that were made
        water = [x for x in water if x is not None]
        # HACK: do this because merging everything all at once loads it all into memory and crashes
        gc.collect()
        run_what = ['python', SCRIPTS_DIR + '/gdal_merge.py', '-co', 'COMPRESS=DEFLATE', '-o', merged_tif, polywater_tif] + water
        CWD = os.path.realpath('.')
        process = subprocess.Popen(run_what,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   creationflags=0x08000000,
                                   cwd=CWD)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception('Error processing merge: ' + stderr)
        gc.collect()
    return merged_tif

def clip_fuel(fp, zone):
    # fp = os.path.join(EXTRACTED_DIR, r'fbp\fuel_layer\FBP_FuelLayer.tif')
    # zone = 14.5
    out_tif = os.path.join(DIR, 'fuel_{}'.format(zone).replace('.', '_')) + '.tif'
    if os.path.exists(out_tif):
        return out_tif
    print(out_tif)
    base_tif, cols, rows, no_data = check_base(fp, zone)
    nowater_tif = check_nowater(base_tif, zone, cols, rows, no_data)
    filled_tif = check_filled(base_tif, nowater_tif, zone, cols, rows, no_data)
    merged_tif = check_merged(filled_tif, zone, cols, rows)
    # finally, copy result to output location
    ds = gdal.Open(merged_tif, 1)
    dst_ds = DRIVER_TIF.CreateCopy(out_tif, ds, 0, options=CREATION_OPTIONS)
    dst_ds = None
    ds = None
    # not sure why this wouldn't copy nodata value but it didn't have one
    ds = gdal.Open(out_tif, 1)
    rb = ds.GetRasterBand(1)
    # HACK: for some reason no_data is a double??
    #~ if no_data is None:
    no_data = int(-math.pow(2, 15) - 1)
    rb.SetNoDataValue(no_data)
    rb.FlushCache()
    rb = None
    ds = None
    gc.collect()
    return out_tif

def make_zone(zone):
    print('Making zone {}'.format(zone))
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
    fbp = clip_fuel(FUEL_RASTER, zone)
    gc.collect()

from multiprocessing import Process, Queue

def makeTiles():
    import itertools
    # HACK: this adds CREATION_OPTIONS items with a '-co' in front of each
    run_what = list(itertools.chain.from_iterable(([['python', SCRIPTS_DIR + '/gdal_retile.py']] +
                                                    map(lambda x: ['-co', x], CREATION_OPTIONS) +
                                                    [['-v', '-ps', '32000', '32000', '-overlap', '16000', '-targetDir', TILED_DIR]])))
    CWD = os.path.realpath(DIR)
    print(run_what)
    for file in os.listdir(DIR):
        print(file)    
        process = subprocess.Popen(run_what + [os.path.join(DIR, file)],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   creationflags=0x08000000,
                                   cwd=CWD)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception('Error processing merge: ' + stderr)

if __name__ == "__main__":
    if not os.path.exists(INT_FUEL):
        os.makedirs(INT_FUEL)
    zone = ZONE_MIN
    while zone <= ZONE_MAX:
        # HACK: use a Process to hopefully get around memory issues
        p = Process(target=make_zone, args=(zone,))
        p.start()
        p.join()
        #make_zone(zone)
        zone += 0.5
    if not os.path.exists(TILED_DIR):
        os.makedirs(TILED_DIR)
        makeTiles()

