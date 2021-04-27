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

from Settings import Settings

##########################
# https://stackoverflow.com/questions/3662361/fill-in-missing-values-with-nearest-neighbour-in-python-numpy-masked-arrays

from scipy import ndimage as nd

import sys
sys.path.append(os.path.join(os.path.dirname(sys.executable), 'Scripts'))
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
TMP = os.path.realpath('/FireGUARD/data/tmp')
CREATION_OPTIONS = ['TILED=YES', 'BLOCKXSIZE=256', 'BLOCKYSIZE=256', 'COMPRESS=LZW']
EARTHENV = os.path.join(DATA_DIR, 'GIS/input/elevation/EarthEnv.tif')

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

def checkAddLakes(zone, cols, rows, for_what, path_gdb, layer):
    print('Adding {}'.format(for_what))
    int_dir = os.path.join(INTERMEDIATE_DIR, 'fuel')
    polywater_tif = os.path.join(int_dir, 'polywater_{}'.format(zone).replace('.', '_')) + '.tif'
    outputShapefile = os.path.join(int_dir, 'projected_{}_{}'.format(for_what, zone).replace('.', '_') + '.shp')
    outputRaster = os.path.join(int_dir, 'water_{}_{}'.format(for_what, zone).replace('.', '_') + '.tif')
    driver_shp = ogr.GetDriverByName('ESRI Shapefile')
    driver_tif = gdal.GetDriverByName('GTiff')
    driver_gdb = ogr.GetDriverByName("OpenFileGDB")
    if not os.path.exists(outputShapefile):
        gdb = driver_gdb.Open(path_gdb, 0)
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
            raster_path = os.path.join(int_dir, 'raster_{}'.format(zone).replace('.', '_') + '.shp')
            # Remove output shapefile if it already exists
            if os.path.exists(raster_path):
                driver_shp.DeleteDataSource(raster_path)
            # Create the output shapefile
            rasterSource = driver_shp.CreateDataSource(raster_path)
            rasterLayer = rasterSource.CreateLayer('raster', lakes_ref, geom_type=ogr.wkbPolygon)
            featureDefn = rasterLayer.GetLayerDefn()
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(rasterGeometry)
            rasterLayer.CreateFeature(feature)
            feature = None
            tmp_path = os.path.join(int_dir, 'bounds_{}'.format(zone).replace('.', '_') + '.shp')
            # delete for now but name nicely in case we want to reuse existing
            if os.path.exists(tmp_path):
                driver_shp.DeleteDataSource(tmp_path)
            source = driver_shp.CreateDataSource(tmp_path)
            # tmpLayer = source.CreateLayer('FINAL', lakes_ref, geom_type=ogr.wkbMultiPolygon)
            tmpLayer = source.CreateLayer('tmp', lakes_ref, geom_type=ogr.wkbMultiPolygon)
            ogr.Layer.Clip(lakes, rasterLayer, tmpLayer)
            coordTrans = osr.CoordinateTransformation(lakes_ref, raster_ref)
            print('Reprojecting...')
            # if os.path.exists(outputShapefile):
                # driver_shp.DeleteDataSource(outputShapefile)
            outDataSet = driver_shp.CreateDataSource(outputShapefile)
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
        outDataSet = driver_shp.Open(outputShapefile)
        outLayer = outDataSet.GetLayer()
        ds = driver_tif.Create(outputRaster, cols, rows, 1, gdal.GDT_UInt16)
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

def clip_fuel(fp, zone):
    # fp = os.path.join(EXTRACTED_DIR, r'fbp\fuel_layer\FBP_FuelLayer.tif')
    # zone = 14.5
    out_tif = os.path.join(DIR, 'fuel_{}'.format(zone).replace('.', '_')) + '.tif'
    if os.path.exists(out_tif):
        return out_tif
    print(out_tif)
    int_dir = os.path.join(INTERMEDIATE_DIR, 'fuel')
    if not os.path.exists(int_dir):
        os.makedirs(int_dir)
    base_tif = os.path.join(int_dir, 'base_{}'.format(zone).replace('.', '_')) + '.tif'
    tmp_tif = os.path.join(int_dir, 'tmp_{}'.format(zone).replace('.', '_')) + '.tif'
    nowater_tif = os.path.join(int_dir, 'nowater_{}'.format(zone).replace('.', '_')) + '.tif'
    polywater_tif = os.path.join(int_dir, 'polywater_{}'.format(zone).replace('.', '_')) + '.tif'
    merged_tif = os.path.join(int_dir, 'merged_{}'.format(zone).replace('.', '_')) + '.tif'
    filled_tif = os.path.join(int_dir, 'filled_{}'.format(zone).replace('.', '_')) + '.tif'
    driver_tif = gdal.GetDriverByName('GTiff')
    driver_gdb = ogr.GetDriverByName("OpenFileGDB")
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
    if not os.path.exists(base_tif):
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
    # close even though we're opening it in if statement so we know it's closed if we don't enter if
    ds = None
    if not os.path.exists(nowater_tif):
        ds = gdal.Open(base_tif, 1)
        dst_ds = driver_tif.CreateCopy(tmp_tif, ds, 0, options=CREATION_OPTIONS)
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
        # want a copy of this before we add the water back in so we can fill from non-water
        dst_ds = driver_tif.CreateCopy(nowater_tif, ds, 0, options=CREATION_OPTIONS)
        dst_ds = None
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
        ft = np.zeros((input.ndim,) + input.shape,
                                dtype=np.int32)
        # ft = np.zeros((input.ndim,) + input.shape,
                                # dtype=np.uint16)
        _nd_image.euclidean_feature_transform(input, sampling, ft)
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
        dst_ds = driver_tif.CreateCopy(filled_tif, ds, 0, options=CREATION_OPTIONS)
        dst_ds = None
        ds = gdal.Open(filled_tif, 1)
        rb = ds.GetRasterBand(1)
        rb.WriteArray(filled, 0, 0)
        # rb.WriteArray(vals_nowater[tuple(ft)], 0, 0)
        rb.FlushCache()
        rb = None
        ds = None
    # now the nodata values should all be filled, so apply the water from the polygons
    if not os.path.exists(merged_tif):
        ds_filled = gdal.Open(filled_tif, 1)
        dst_ds = driver_tif.CreateCopy(polywater_tif, ds_filled, 0, options=CREATION_OPTIONS)
        dst_ds = None
        ds_filled = None
        gc.collect()
        print('Adding water from polygons')
        water = [checkAddLakes(zone, cols, rows, 'USA', r'C:\FireGUARD\data\extracted\nhd\NHD_H_National_GDB.gdb', r'NHDWaterbody')]
        for prov in ['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT']:
            path_gdb = r'C:\FireGUARD\data\extracted\canvec\canvec_50K_{}_Hydro.gdb'.format(prov)
            water += [checkAddLakes(zone, cols, rows, prov, path_gdb, 'waterbody_2')]
        # should have a list of rasters that were made
        water = [x for x in water if x is not None]
        #~ merge_what = [polywater_tif] + water
        #~ g = gdal.Warp(merged_tif, merge_what, format="GTiff", options=["COMPRESS=LZW", "TILED=YES"])
        #~ g = None
        #~ src_files = map(rasterio.open, water)
        # HACK: do this because merging everything all at once loads it all into memory and crashes
        gc.collect()
        ################################
        #~ mosaic = rasterio.open(polywater_tif)
        #~ while len(water) > 0:
            #~ old_mosaic = mosaic
            #~ cur_file = water.pop()
            #~ print('Merging ' + cur_file)
            #~ cur = rasterio.open(cur_file)
            #~ mosaic, out_trans = merge([cur, old_mosaic])
            #~ out_meta = cur.meta.copy()
            #~ cur = None
            #~ old_mosaic = None
            #~ with rasterio.open(merged_tif, "w", **out_meta) as dest:
                #~ dest.write(mosaic)
            #~ gc.collect()
            #~ if len(water) > 0:
                #~ mosaic = rasterio.open(merged_tif)
        ################################
        #~ mosaic, out_trans = merge(src_files)
        #~ mosaic = rasterio.open(
        #~ for f in src_files:
            #~ f.close()
        #~ src_files = None
        #~ ds_filled = gdal.Open(polywater_tif, 1)
        #~ dst_ds = driver_tif.CreateCopy(merged_tif, ds_filled, 0, options=CREATION_OPTIONS)
        #~ dst_ds = None
        #~ ds_filled = None
        #~ for w in water:
            #~ gm.main(['', '-o', merged_tif, merged_tif] + [w])
        #~ try:
            #~ gc.collect()
        gm.main(['', '-co', 'COMPRESS=DEFLATE', '-o', merged_tif, polywater_tif] + water)
        #~ except Exception as e:
            #~ print(e)
            #~ if os.path.exists(merged_tif):
                #~ os.remove(merged_tif)
            #~ sys.exit(-1)
        # lakes should have been burned into polywater_tif
    # finally, copy result to output location
    ds = gdal.Open(merged_tif, 1)
    dst_ds = driver_tif.CreateCopy(out_tif, ds, 0, options=CREATION_OPTIONS)
    dst_ds = None
    ds = None
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
    fbp = clip_fuel(os.path.join(EXTRACTED_DIR, r'fbp\fuel_layer\FBP_FuelLayer.tif'), zone)
    gc.collect()
    zone += 0.5
