"""Create FBP fuel rasters from eFRI data and other inputs"""
from __future__ import print_function

# NOTE: seems to need to be run in ArcMap for:
# - the USA water

CELLSIZE_M = 100
import pandas as pd

# HACK: import this so that we don't get error on sys.stdout.flush()
import sys
from sys import stdout
import os

#~ HOME_DIR = os.path.dirname(os.path.realpath(__import__("__main__").__file__))
HOME_DIR = "C:\\FireGUARD\\GIS"
sys.path.append(HOME_DIR)
os.chdir(HOME_DIR)
sys.path.append(os.path.join(HOME_DIR, 'fbp_convert'))
import sys
sys.path.append('..\util')
import common
import unpack

import shared
#~ reload(shared)
from shared import *
import fuelconversion
#~ reload(fuelconversion)
from util import ensure_dir
from FuelLookup import *

GIS = r'C:\FireGUARD\data\GIS'
GIS_SHARE = common.CONFIG.get('FireGUARD', 'gis_share')
INPUT = os.path.join(GIS, "input")
GIS_ELEVATION = os.path.join(INPUT, "elevation")
GIS_FIRE = os.path.join(INPUT, 'fire')
GIS_FUELS = os.path.join(INPUT, 'fuels')
GIS_WATER = os.path.join(INPUT, 'water')
INTERMEDIATE = os.path.join(GIS, "intermediate")
DOWNLOADED = os.path.join(GIS, "downloaded")
OUTPUT = ensure_dir(os.path.join(INTERMEDIATE, "fuels"))
GENERATED = ensure_dir(os.path.join(GIS, "generated", "fuels"))
TIF_OUTPUT = ensure_dir(os.path.join(GENERATED, "out_{:03d}m".format(CELLSIZE_M)))
BOUNDS_DIR = ensure_dir(os.path.join(OUTPUT, "01_bounds"))
WATER_DIR = ensure_dir(os.path.join(OUTPUT, "02_water"))
NTL_DIR = ensure_dir(os.path.join(OUTPUT, "03_ntl"))
WATER_BOUNDS_DIR = ensure_dir(os.path.join(OUTPUT, "04_waterbounds"))
NTL_FILL_DIR = ensure_dir(os.path.join(OUTPUT, "05_ntl_fill"))
FUEL_BASE_DIR = ensure_dir(os.path.join(OUTPUT, "06_fuel_base"))
FUEL_RASTER_DIR = ensure_dir(os.path.join(OUTPUT, "07_fuel_raster"))
FUEL_MOSAIC_DIR = ensure_dir(os.path.join(OUTPUT, "08_fuel_mosaic"))
FUEL_DIR = ensure_dir(os.path.join(OUTPUT, "09_fuel"))
FUEL_JOIN_DIR = ensure_dir(os.path.join(OUTPUT, "10_fuel_join"))
CANVEC_FOLDER = os.path.realpath(os.path.join(GIS, '../extracted/canvec/'))


POLY_GDB = checkGDB(OUTPUT, "processed.gdb")
PROCESSED_GDB = checkGDB(OUTPUT, "processed_{:03d}m.gdb".format(CELLSIZE_M))
BOUNDS_GDB = checkGDB(BOUNDS_DIR, "bounds.gdb")

## NDD Non-sensitive data from share
NDD_NON = os.path.join(GIS_SHARE, "NDD", "GDDS-Internal-MNRF.gdb")

mask_LIO_gdb = os.path.join(OUTPUT, "{}_LIO.gdb")
## DEM made by combining EarthEnv data into a TIFF
EARTHENV = os.path.join(GIS_ELEVATION, "EarthEnv.tif")

FIRE_DISTURBANCE = os.path.join(GIS_FIRE, r'FIRE_DISTURBANCE_AREA.shp')
DEM_BOX_SIZE_KM = 50
BUFF_DIST = "{} kilometers".format(DEM_BOX_SIZE_KM)
DEM_BOX = None

# NOTE: this only applies where there's no national layer or no LIO data
LIO_CELL_BUFFER = 50

# use this so that we process them sequentially
import collections
projections = collections.OrderedDict()
projections[14.5] = { 'CentralMeridian': -96.0 }
projections[15.0] = { 'CentralMeridian': -93.0 }
projections[15.5] = { 'CentralMeridian': -90.0 }
projections[16.0] = { 'CentralMeridian': -87.0 }
projections[16.5] = { 'CentralMeridian': -84.0 }
projections[17.0] = { 'CentralMeridian': -81.0 }
projections[17.5] = { 'CentralMeridian': -78.0 }
projections[18.0] = { 'CentralMeridian': -75.0 }

# base our projected zones off of UTM Zone 15N but change the Central Meridian for each
ZONES = projections.keys()

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--zones", help="any of {}".format(ZONES))
parser.add_argument("--split", action="store_true", help="split output rasters")
parser.add_argument("--force", action="store_true", help="force generating fuels databases")
parser.add_argument("--fbp", action="store_true", help="update FBP classifications")
# HACK: do this so that if we manually set args while debugging they don't get overridden
try:
    if not args:
        args = parser.parse_args()
except:
    # this will throw if we haven't done this yet
    args = parser.parse_args()
    #~ if 0 == len(''.join(sys.argv)):
        # this means we're in arcmap?
        #~ args.zones = '14.5,16.5'
        #~ args.zones = '15.0,17.0'
        #~ args.zones = '15.5,17.5'
        #~ args.zones = '16.0,18.0'
        #~ args.zones = '14.5'
        #~ args.zones = '15.0'
        #~ args.zones = '15.5'
        #~ args.zones = '16.0'
        #~ args.zones = '16.5'
        #~ args.zones = '17.0'
        #~ args.zones = '17.5'
        #~ args.zones = '18.0'
        #~ args.fbp = True
        #~ args.force = True
#~ args.split = True
DO_SPLIT = args.split
FORCE = args.force
DO_FBP = args.fbp
if args.zones:
    arg_zones = [float(x.strip()) for x in args.zones.split(',')]
    for x in arg_zones:
        if x not in ZONES:
            print("Invalid zone: " + str(x))
            print(parser.format_help())
            sys.exit(-1)
    ZONES = [x for x in ZONES if x in arg_zones]


# USA National Hydrography Dataset
# https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/National/HighResolution/GDB/NHD_H_National_GDB.zip
NHD_GDB = os.path.join(GIS_WATER, "NHD_H_National_GDB.gdb")
lakes_nhd = os.path.join(NHD_GDB, "Hydrography", "NHDWaterbody")
lakes_nhd_area = os.path.join(NHD_GDB, "Hydrography", "NHDArea")

if not (os.path.exists(lakes_nhd) and os.path.exists(lakes_nhd_area)):
    common.save_http(DOWNLOADED, r'https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/National/HighResolution/GDB/NHD_H_National_GDB.zip')
    unpack.check_zip(DOWNLOADED, '*', file_mask='NHD_H_National_GDB.zip', output=GIS_WATER)

canada = os.path.join(INPUT, "canada\\lcsd000a19a_e.shp")

if not os.path.exists(canada):
    common.save_http(DOWNLOADED, r'http://www12.statcan.gc.ca/census-recensement/2011/geo/bound-limit/files-fichiers/lcsd000a19a_e.zip')
    unpack.check_zip(DOWNLOADED, '*', file_mask='lcsd000a19a_e.zip', output=os.path.join(INPUT, 'canada'))

national = os.path.join(GIS_FUELS, r'national\fuel_layer\FBP_FuelLayer_wBurnscars.tif')

if not os.path.exists(national):
    common.save_http(GIS_FUELS, r'https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/Canadian_Forest_FBP_Fuel_Types_v20191114.zip')
    unpack.check_zip(GIS_FUELS, '*', output=os.path.join(GIS_FUELS, 'national'))
PROJECTION_BASE = arcpy.SpatialReference(3159).exportToString().replace("15N","{}N").replace("-93.0","{}")

# NOTE: use 645 instead of 650 because that's what it was before and we don't know why
dct_ntl = {
    98: 104,
    99: 103,
    101: 1,
    102: 2,
    103: 3,
    104: 4,
    105: 5,
    106: 6,
    107: 7,
    108: 13,
    109: 645,
    111: 950,
    113: 21,
    114: 22,
    115: 23,
    116: 31,
    118: 102,
    119: 101,
    120: 105,
    121: 101,
    122: 105,
}

dct_2018 = {}
# fix mixedwood not being generic
for x in xrange(0, 100, 1):
    dct_2018[400 + x] = 600 + x
    dct_2018[500 + x] = 600 + x
    dct_2018[700 + x] = 900 + x
    dct_2018[800 + x] = 900 + x
# fix D2 being used for lichen and mosses in the far north
dct_2018[12] = 105
# change D1 to D1/D2
dct_2018[11] = 13
for x in xrange(1, 1000):
    if not dct_2018.has_key(x):
        dct_2018[x] = x

# have these functions so we make sure we always use the right type when copying each type of raster
def copyFuel(in_raster, out_raster):
    arcpy.CopyRaster_management(in_raster, out_raster, pixel_type="16_BIT_UNSIGNED", nodata_value="0")


def copyDEM(in_raster, out_raster):
    arcpy.CopyRaster_management(in_raster, out_raster, pixel_type="16_BIT_SIGNED")


def copyAspect(in_raster, out_raster):
    arcpy.CopyRaster_management(in_raster, out_raster, pixel_type="16_BIT_UNSIGNED")


def copySlope(in_raster, out_raster):
    arcpy.CopyRaster_management(in_raster, out_raster, pixel_type="8_BIT_UNSIGNED")


def create_projection(zone):
    result = arcpy.SpatialReference()
    result.loadFromString(PROJECTION_BASE.format(zone, projections[zone]['CentralMeridian']))
    return result

def selectOverlap(base, intersect, output, makeEmpty=True):
    lyr = arcpy.CreateScratchName()
    arcpy.MakeFeatureLayer_management(base, lyr)
    arcpy.SelectLayerByLocation_management(lyr, "INTERSECT", intersect)
    count = int(arcpy.GetCount_management(lyr)[0])
    if makeEmpty or count > 0:
        arcpy.CopyFeatures_management(lyr, output)
    arcpy.Delete_management(lyr)
    if count == 0 and not makeEmpty:
        return None
    return output


def create_grid(zone):
    zone_fixed = '{}'.format(zone).replace('.', '_')
    def makeDEM(_):
        zone_dir = ensure_dir(os.path.join(BOUNDS_DIR, 'zone_{}'.format(zone_fixed)))
        # \1
        env_push()
        env_defaults(workspace=checkGDB(zone_dir, 'grids_{}m.gdb'.format(gridSize)),
                     cellSize=CELLSIZE_M)
        Projection = create_projection(zone)
        # determine extent in zone that we're looking for
        print("Changing projection to {}".format(Projection.name))
        arcpy.env.outputCoordinateSystem = Projection
        print("Creating {}m grid for {}".format(gridSize, Projection.name))
        country = project(canada, "canada", Projection)
        bounds = check_make("bounds", lambda _: arcpy.Buffer_analysis(country, _, BUFF_DIST))
        print("Creating large grid for zone {}".format(zone))
        # create a grid that's got the core part of the zone without worry about edges since we'll have others for that
        # \2
        env_push()
        arcpy.env.outputCoordinateSystem = Projection
        zoneBounds = check_make("ZoneBounds", lambda _: arcpy.CreateFishnet_management(_,
                                                                                       "300000 4000000",
                                                                                       "300000 4000010",
                                                                                       "{}".format(bigGridSize_m),
                                                                                       "{}".format(bigGridSize_m),
                                                                                       "0",
                                                                                       "0",
                                                                                       "700000 7000000",
                                                                                       "NO_LABELS",
                                                                                       "300000 4000000 700000 7000000",
                                                                                       "POLYGON"))
        env_pop()
        # /2
        #~ outerBounds = check_make("OuterBounds", lambda _: arcpy.Dissolve_management("ZoneBounds", _, "", "", "MULTI_PART", "DISSOLVE_LINES"))
        boundClip = check_make("BoundClip", lambda _: arcpy.Clip_analysis(zoneBounds, bounds, _))
        finalBounds = check_make("Area", lambda _: arcpy.MinimumBoundingGeometry_management(boundClip, _, "ENVELOPE", "ALL"))
        boundsBuffer = check_make("BoundsBuffer", lambda _: arcpy.Buffer_analysis(finalBounds, _, "20 Kilometers"))
        zoneGrid = check_make("ZoneGrid", lambda _: selectOverlap(zoneBounds, boundsBuffer, _))
        zoneBuffer = check_make("ZoneBuffer", lambda _: arcpy.Buffer_analysis(zoneGrid, _, "20 Kilometers", dissolve_option="ALL"))
        DEM_clip = calc("DEM_clip", lambda _: clip_raster_box(EARTHENV, zoneBuffer, _), buildPyramids=False)
        def mkMask(input):
            full_extent = arcpy.Describe(input).extent
            print(full_extent)
            # use the bounding box of the first big grid cell that isn't missing cells inside (as per above)
            xMin = int(round(full_extent.XMin / gridSize, 0)) * gridSize
            yMin = int(round(full_extent.YMin / gridSize, 0)) * gridSize
            xMax = int(round(full_extent.XMax / gridSize, 0)) * gridSize
            yMax = int(round(full_extent.YMax / gridSize, 0)) * gridSize
            assert (xMin < xMax)
            assert (yMin < yMax)
            print("Bounds for raster are: ({}, {}), ({}, {})".format(xMin, yMin, xMax, yMax))
            mask = CreateConstantRaster(0, "INTEGER", gridSize, full_extent)
            arcpy.DefineProjection_management(mask, Projection.exportToString())
            return mask
        mask = calc("Zone", lambda _: mkMask(zoneGrid))
        mask = calc("Buffer", lambda _: mkMask(zoneBuffer))
        # \2
        env_push()
        env_defaults(mask=mask,
                     snapAndExtent=mask)
        arcpy.env.outputCoordinateSystem = Projection
        dem = check_make("DEM_project", lambda _: project_raster(DEM_clip, _, gridSize, "BILINEAR", Projection))
        checkGDB(os.path.dirname(_))
        copyDEM(dem, _)
        env_pop()
        # /2
        env_pop()
        # /1
    return check_make(os.path.join(GENERATED, "dem_{:03d}m.gdb".format(CELLSIZE_M), "dem_{}".format(zone_fixed)), makeDEM)


def make_grid(zones, showIntermediate=False):
    print("Generating grid for zones {}".format(zones))
    origAddOutputsToMap = arcpy.env.addOutputsToMap
    arcpy.env.addOutputsToMap = showIntermediate
    outputs = []
    i = 0
    for zone, params in projections.iteritems():
        if zone in zones:
            i += 1
            print("Processing zone {} of {}".format(i, len(zones)))
            projections[zone]['ZoneGrid'] = create_grid(zone)
            outputs += [projections[zone]['ZoneGrid']]
    arcpy.env.addOutputsToMap = origAddOutputsToMap

def makeWater(province, water_projected, erase=None, orig=None, clear=True, sql=None, clip=None):
    if not orig:
        orig = os.path.join(CANVEC_FOLDER, "canvec_50K_{}_Hydro.gdb\\waterbody_2".format(province))
    last = orig
    if clip:
        last = check_make("water_{}_clip".format(province), lambda _: arcpy.Clip_analysis(last, clip, _))
    if sql:
        last = check_make("water_{}_select".format(province), lambda _: arcpy.Select_analysis(last, _, sql))
    if clear:
        last = check_make("water_{}_no_fields".format(province), lambda _: clearData(last, _))
    projected = os.path.join(water_projected, "WATER_{}_project".format(province))
    last = project(last, projected)
    if erase is not None:
        last = check_make("water_{}".format(province), lambda _: arcpy.Erase_analysis(last, erase, _))
    else:
        last = check_make("water_{}".format(province), lambda _: arcpy.CopyFeatures_management(last, _))
    return last

def mkFuel(zone_name, buffer, fuel_buffer, projection):
    grid_gdb = checkGDB(ensure_dir(os.path.join(BOUNDS_DIR, zone_name)), 'grids_{}m.gdb'.format(gridSize))
    # \1
    env_push()
    env_defaults(mask=fuel_buffer,
                 snapAndExtent=buffer)
    # \2
    env_push()
    env_defaults(workspace=checkGDB(ensure_dir(os.path.join(NTL_DIR, zone_name)), 'ntl_{}m.gdb'.format(gridSize)), mask="", extent="", snapRaster=buffer, cellSize=CELLSIZE_M)
    ntl_clip = calc("ntl_clip", lambda _: clip_raster_box(national_reclassify, fuel_buffer, _), buildPyramids=False)
    # keep entire grid because we need to fill in from outside
    ntl_project = calc("ntl_project", lambda _: project_raster(ntl_clip, _, cellsize_m=CELLSIZE_M, projection=projection))
    ntl_nowater = calc("ntl_nowater", lambda _: SetNull(ntl_project == 102, ntl_project))
    env_pop()
    # /2
    # \2
    env_push()
    env_defaults(workspace=checkGDB(ensure_dir(os.path.join(WATER_DIR, zone_name)), 'water_{}m.gdb'.format(gridSize)))
    water_select = check_make("water_select", lambda _: selectOverlap(WATER, fuel_buffer, _))
    water_proj = project(water_select, "water_proj", projection)
    water_raster = calc("water_raster", lambda _: arcpy.FeatureToRaster_conversion(water_proj, "gridcode", _, CELLSIZE_M))
    env_pop()
    # /2
    env_push()
    env_defaults(mask="", snapAndExtent="", workspace=checkGDB(ensure_dir(os.path.join(WATER_BOUNDS_DIR, zone_name)), 'water_{}m.gdb'.format(gridSize)))
    bounds_water = calc("bounds_water", lambda _: Con(IsNull(ntl_project), ntl_project, Con(IsNull(water_raster), ntl_nowater, water_raster)))
    bounds_mask = calc_mask("bounds_mask", bounds_water)
    FILL_SIZE = 10
    bounds_filled = calc("bounds_filled", lambda _: arcpy.sa.Con(arcpy.sa.IsNull(bounds_mask),arcpy.sa.FocalStatistics(bounds_mask,
                                                                   arcpy.sa.NbrRectangle(FILL_SIZE, FILL_SIZE),'MAJORITY'), bounds_mask))
    # shrink back down so edges don't end up with euclidean
    bounds_shrink = calc("bounds_shrink", lambda _: Shrink(bounds_filled, FILL_SIZE / 2, [0]))
    # need to fill in vertical edges
    bounds_all = calc("bounds_all", lambda _: Con(IsNull(water_raster), bounds_shrink, water_raster))
    bounds_nowater = calc("bounds_nowater", lambda _: SetNull(bounds_all == 102, bounds_all))
    env_pop()
    # /2
    # \2
    env_push()
    env_defaults(mask=bounds_nowater, snapAndExtent=buffer,
                 workspace=checkGDB(ensure_dir(os.path.join(NTL_FILL_DIR, zone_name)), 'ntl_{}m.gdb'.format(gridSize)))
    fuel_euclidean = check_make("fuel_euclidean", lambda _: arcpy.gp.EucAllocation_sa(ntl_nowater, _, "", "", CELLSIZE_M, "Value", "fuel_euclidean_distance", "fuel_euclidean_direction"))
    # \3
    env_push()
    env_defaults(snapAndExtent=buffer, mask="")
    fuel_filled = calc("fuel_filled", lambda _: Con(IsNull(water_raster), fuel_euclidean, water_raster))
    # /3
    env_pop()
    # /2
    env_pop()
    fuel_gdb = checkGDB(ensure_dir(os.path.join(FUEL_DIR, zone_name)), 'fuel_{}m.gdb'.format(gridSize))
    # \2
    env_push()
    env_defaults(workspace=fuel_gdb, mask=buffer, snapAndExtent=buffer)
    def runLIO(number, name):
        grid_dir = ensure_dir(os.path.join(os.path.dirname(fuel_gdb), name))
        print("Finding {} data".format(name))
        # convert to raster
        def ensureLIO(_):
            base_gdb = os.path.join(ensure_dir(os.path.join(FUEL_BASE_DIR, zone_name)), "{}_{}.gdb".format(number, name))
            # elev_out = os.path.join(GENERATED, 'elev_{:03d}m.tif'.format(CELLSIZE_M))
            # using ontario data actually seems to make DEM worse since it's weird around the provincial borders
            # we don't really need floating point precision??
            # elev_out = check_make(elev_out, lambda _: copyDEM(EarthEnv, _))
            features = sorted(getFeatures(mask_LIO_gdb.format(name)))
            # find overlap with LIO layers
            def makeBaseGDB(_):
                env_push()
                env_defaults(workspace=checkGDB(_))
                for f in features:
                    def doLayer(_):
                        #~ selectOverlap(f, fuel_buffer, _, False)
                        #~ (base, intersect, output, makeEmpty=True)
                        base = f
                        intersect = fuel_buffer
                        output = _
                        makeEmpty = False
                        lyr = arcpy.CreateScratchName()
                        arcpy.MakeFeatureLayer_management(base, lyr)
                        arcpy.SelectLayerByLocation_management(lyr, "INTERSECT", intersect)
                        # remove invalid
                        arcpy.SelectLayerByAttribute_management(lyr, "REMOVE_FROM_SELECTION", "POLYTYPE = 'XXX'")
                        count = int(arcpy.GetCount_management(lyr)[0])
                        if makeEmpty or count > 0:
                            arcpy.CopyFeatures_management(lyr, output)
                            # repair this because when it was copied it was projected
                            arcpy.RepairGeometry_management(lyr)
                        arcpy.Delete_management(lyr)
                        if count == 0 and not makeEmpty:
                            return None
                        return output
                    check_make(os.path.basename(f), doLayer)
                env_pop()
            grid_workspace = os.path.join(FUEL_RASTER_DIR, zone_name, "{}_{}_{:03d}m".format(number, name, CELLSIZE_M))
            base_gdb = check_make(base_gdb, makeBaseGDB, FORCE and not arcpy.Exists(grid_workspace))
            def makeGridGDB(_):
                # call this every time we make this so that we don't need to re-run it outside and get polygons again
                if DO_FBP:
                    fuelconversion.FRI2FBP2016(base_gdb)
                env_push()
                # clear this because some rasters crash
                env_defaults(workspace=ensure_dir(_), mask=None, extent=None, cellSize=None, pyramid=None)
                arcpy.env.outputCoordinateSystem = None
                env_push()
                # This crashes when trying to use gdb, so use TIFFs
                env_clear()
                arcpy.env.mask = None
                arcpy.env.snapRaster = buffer
                for f in sorted(getFeatures(base_gdb)):
                    if countRows(f) == 0:
                        raise Exception("Error - no features in input {}".format(f))
                    def mkRaster(_):
                        arcpy.FeatureToRaster_conversion(f, "FBPvalue", _, CELLSIZE_M)
                    to_raster = os.path.join(_, os.path.basename(f) + ".tif")
                    print(to_raster)
                    r = calc(to_raster, mkRaster, buildPyramids=False)
                env_pop()
                env_pop()
            # crashes when trying to mosaic when using gdb, so use TIFF
            grid_workspace = check_make(grid_workspace, makeGridGDB, FORCE)
            env_push()
            env_defaults(workspace=ensure_dir(os.path.join(FUEL_MOSAIC_DIR, zone_name, "{}_{}_filter_{:03d}m".format(number, name, CELLSIZE_M))))
            def mkUnfiltered(_):
                # HACK: assume something made it into the raster already
                rasters = sorted(getRasters(grid_workspace))
                print("Adding {}".format(raster_path(rasters[0])))
                copyFuel(rasters[0], _)
                for r in rasters[1:]:
                    print("Adding {}".format(raster_path(r)))
                    arcpy.Mosaic_management(r, _)
            # NOTE: these rasters look really wrong along the edges but the next step cleans that up
            unfiltered = calc(os.path.join(arcpy.env.workspace, 'unfiltered.tif'), mkUnfiltered)
            # keep unclassified but not non-fuel or Unknown
            filtered = calc('filtered.tif', lambda _: SetNull(unfiltered == 101, SetNull(unfiltered == 103, unfiltered)))
            filter_mask = calc_mask('mask_filtered.tif', filtered)
            filter_buffer = calc('buffer_filtered.tif', lambda _: Expand(filter_mask, LIO_CELL_BUFFER, [0]))
            # remove water because we trust the polygons we used before more
            nowater = calc('nowater.tif', lambda _: SetNull(filtered == 102, filtered))
            env_pop()
            env_push()
            env_defaults(mask=filter_buffer)
            fuel_euclidean = calc("fuel_euclidean", lambda _: arcpy.gp.EucAllocation_sa(nowater, _, "", "", CELLSIZE_M, "Value", "fuel_euclidean_distance", "fuel_euclidean_direction"))
            env_pop()
            # override everything with water, but only use the euclidean where the original non-euclidean national layer doesn't exist
            return calc(_, lambda _: Con(IsNull(water_raster), Con(IsNull(ntl_nowater), fuel_euclidean, nowater), water_raster), FORCE)
        fuel_lio_only = check_make("fuel_{}_only".format(name), ensureLIO, FORCE)
        return fuel_lio_only
    fuel_last = fuel_efri_only = runLIO(1, 'efri')
    # /2
    env_pop()
    env_push()
    env_defaults(workspace=checkGDB(ensure_dir(os.path.join(FUEL_JOIN_DIR, zone_name)), 'fuel_{}m.gdb'.format(gridSize)))
    fuel_last = fuel_efri_ntl = calc('fuel_efri_ntl', lambda _: Con(IsNull(fuel_efri_only), fuel_filled, fuel_efri_only), FORCE)
    fires = calc("fires", lambda _: arcpy.FeatureToRaster_conversion(FIRE_DISTURBANCE, "FIRE_YEAR", _, CELLSIZE_M))
    cur_year = datetime.datetime.now().year
    fuel_years = [101, 104, 104, 105, 105, 625, 625, 625, 625, 625]
    fire_years = []
    for i in xrange(len(fuel_years)):
        fire_years.append(calc("fires_{:02d}".format(i), lambda _: Con(fires == (cur_year - i), fuel_years[i])).catalogPath)
    water = calc("water", lambda _: SetNull(fuel_efri_ntl != 102, fuel_efri_ntl))
    inputs = ';'.join([water.catalogPath] + fire_years + [fuel_efri_ntl.catalogPath])
    # HACK: crashing when we try to do this with calc()
    #~ fuel_last = fuel_fires = calc("fuel_fires", lambda _: arcpy.MosaicToNewRaster_management(inputs, arcpy.env.workspace, _, "", "32_BIT_SIGNED", "", 1, "FIRST"))
    if not arcpy.Exists(os.path.join(arcpy.env.workspace, "fuel_fires")):
        arcpy.MosaicToNewRaster_management(inputs, arcpy.env.workspace, "fuel_fires", "", "32_BIT_SIGNED", "", 1, "FIRST")
    fuel_last = fuel_fires = os.path.join(arcpy.env.workspace, "fuel_fires")
    env_pop()
    return fuel_last


def create_fuel(zone):
    print("Creating fuel for zone {}".format(zone))
    fuel_gdb = checkGDB(GENERATED, "fuel_{:03d}m.gdb".format(CELLSIZE_M))
    fuel_final = os.path.join(fuel_gdb, "fuel_{}".format(zone).replace('.', '_'))
    fuel_tif = os.path.join(TIF_OUTPUT, "fuel_{:03d}m_{}.tif".format(CELLSIZE_M, str(zone).replace('.', '_')))
    slope_tif = os.path.join(TIF_OUTPUT, "slope_{:03d}m_{}.tif".format(CELLSIZE_M, str(zone).replace('.', '_')))
    aspect_tif = os.path.join(TIF_OUTPUT, "aspect_{:03d}m_{}.tif".format(CELLSIZE_M, str(zone).replace('.', '_')))
    if not DO_SPLIT and arcpy.Exists(fuel_final) and arcpy.Exists(fuel_tif) and arcpy.Exists(slope_tif) and arcpy.Exists(aspect_tif):
        return fuel_final
    zone_name = 'zone_{}'.format(zone).replace('.', '_')
    grid_gdb = checkGDB(ensure_dir(os.path.join(BOUNDS_DIR, zone_name)), 'grids_{}m.gdb'.format(gridSize))
    env_push()
    env_defaults(workspace=grid_gdb,
                 cellSize=CELLSIZE_M)
    projection = create_projection(zone)
    arcpy.env.outputCoordinateSystem = projection
    # determine extent in zone that we're looking for
    print("Changing projection to {}".format(projection.name))
    buffer = os.path.join(arcpy.env.workspace, "Zone")
    fuel_buffer = os.path.join(arcpy.env.workspace, "ZoneBuffer")
    def check_copy_fuel(_):
        fuel = mkFuel(zone_name, buffer, fuel_buffer, projection)
        copyFuel(fuel, _)
    fuel_final = check_make(fuel_final, check_copy_fuel)
    fuel_tif = calc(fuel_tif, lambda _: copyFuel(fuel_final, _))
    env_push()
    env_defaults(snapAndExtent=fuel_tif)
    dem_gdb = checkGDB(GENERATED, "dem_{:03d}m.gdb".format(CELLSIZE_M))
    dem_out = os.path.join(dem_gdb, "dem_{}".format(zone).replace('.', '_'))
    dem_tif = os.path.join(TIF_OUTPUT, "dem_{:03d}m_{}.tif".format(CELLSIZE_M, str(zone).replace('.', '_')))
    dem_tif = calc(dem_tif, lambda _: copyDEM(dem_out, _))
    slope_float = os.path.join(grid_gdb, "slope_{}".format(zone).replace('.', '_'))
    slope_float = calc(slope_float, lambda _: arcpy.Slope_3d(dem_out, _, "PERCENT_RISE"))
    slope_gdb = checkGDB(GENERATED, "slope_{:03d}m.gdb".format(CELLSIZE_M))
    slope_out = os.path.join(slope_gdb, "slope_{}".format(zone).replace('.', '_'))
    slope_out = calc(slope_out, lambda _: copySlope(slope_float, _))
    slope_tif = calc(slope_tif, lambda _: copySlope(slope_out, _))
    aspect_float = os.path.join(grid_gdb, "aspect_{}".format(zone).replace('.', '_'))
    aspect_float = calc(aspect_float, lambda _: arcpy.Aspect_3d(dem_out, _))
    aspect_gdb = checkGDB(GENERATED, "aspect_{:03d}m.gdb".format(CELLSIZE_M))
    aspect_out = os.path.join(aspect_gdb, "aspect_{}".format(zone).replace('.', '_'))
    aspect_out = calc(aspect_out, lambda _: copyAspect(aspect_float, _))
    aspect_tif = calc(aspect_tif, lambda _: copyAspect(aspect_out, _))
    env_pop()
    if DO_SPLIT:
        split_dir = os.path.join(TIF_OUTPUT, "split")
        ensure_dir(split_dir)
        # can't have more than 32767 rows or columns, but try to make them square
        # cut things up a lot but make them overlap significantly so we can always find an area centered on the fire
        # NOTE: 1.0 ha cells end up with 4001 pixel wide tiffs, so set based on splitting those up vertically
        #~ center_size = 4001.0 / 2
        #~ tilesize = 2.0 * center_size
        #~ overlap = center_size
        #~ # if one tile spans the entire width then don't split it
        #~ # if not 1 tile then make sure it's even # so snapraster still works
        #~ num_tile_columns = 2 * (int(math.ceil(slope_tif.width / float(center_size))) / 2) if tilesize < slope_tif.width else 1
        #~ num_tile_rows = 2 * (int(math.ceil(slope_tif.height / float(center_size))) / 2) if tilesize < slope_tif.height else 1
        # 14.5 1333.66666667 4001.0 1332 1 7
        # 15.0 1333.66666667 4001.0 1332 1 9
        # 15.5
        # 16.0
        # 16.5
        # 17.0
        # 17.5
        # 18.0
        # want to make squares
        DEFAULT_TILE_SIZE = 4002
        center_size = DEFAULT_TILE_SIZE / 3.0
        tilesize = int(3.0 * center_size)
        # make sure this is even so we stay on same snap
        overlap = 2 * int(center_size / 2)
        # if one tile spans the entire width then don't split it
        #~ num_tile_columns = int(math.ceil(slope_tif.width / float(center_size))) if tilesize < slope_tif.width else 1
        #~ num_tile_rows = int(math.ceil(slope_tif.height / float(center_size))) if tilesize < slope_tif.height else 1
        #~ num_tile_columns = 2 * (int(math.ceil(slope_tif.width / float(center_size))) / 2) if tilesize < slope_tif.width else 1
        #~ num_tile_rows = 2 * (int(math.ceil(slope_tif.height / float(center_size))) / 2) if tilesize < slope_tif.height else 1
        #~ num_rasters = "{} {}".format(num_tile_columns, num_tile_rows)
        #~ print(zone, center_size, tilesize, overlap, num_tile_columns, num_tile_rows)
        #~ print("Splitting into {} tiles".format(num_rasters.replace(' ', 'x')))
        tile_size = "{} {}".format(DEFAULT_TILE_SIZE, DEFAULT_TILE_SIZE)
        print("Splitting into {} tiles".format(tile_size.replace(" ", "x")))
        def doSplit(r):
            arcpy.SplitRaster_management(r, split_dir, r.name.replace('.tif', '__'), "SIZE_OF_TILE", "TIFF", tile_size=tile_size, overlap=overlap)
        env_push()
        env_defaults(snapRaster=fuel_tif)
        doSplit(fuel_tif)
        doSplit(dem_tif)
        doSplit(slope_tif)
        doSplit(aspect_tif)
        env_pop()
    env_pop()
    return fuel_final

def getColumns(_):
    return [x.name for x in arcpy.ListFields(_)]

def countRows(_):
    count = 0
    with arcpy.da.SearchCursor(_, [arcpy.Describe(_).OIDFieldName]) as cursor:
        for row in cursor:
            count += 1
    return count

def round_to_nearest(x, base):
    return int(base * math.ceil(float(x) / base))

def getName(_):
    return os.path.basename(str(_))

def fixColumnNames(src, fields):
    actuals = getColumns(src)
    lower = map(lambda _: _.lower(), actuals)
    real = []
    for f in fields:
        assert (f.lower() in lower), "Missing field {} is required".format(f)
        real.append(actuals[lower.index(f.lower())])
    return real

def copyByFields(src, dest, fields):
    maps = arcpy.FieldMappings()
    real_fields = fixColumnNames(src, fields)
    for f in real_fields:
        map = arcpy.FieldMap()
        map.addInputField(src, f)
        maps.addFieldMap(map)
    arcpy.FeatureClassToFeatureClass_conversion(src, os.path.dirname(dest), os.path.basename(dest), "#", maps)

def percentile(n, pct):
    return int(float(n) * float(pct) / 100.0)

if __name__ == '__main__':
    if not arcpy.env.scratchWorkspace:
        arcpy.env.scratchWorkspace = arcpy.env.scratchGDB
    if not arcpy.env.workspace:
        arcpy.env.workspace = arcpy.env.scratchGDB
    print("Processing...")
    # \1
    env_push()
    env_defaults(workspace=POLY_GDB)
    # HACK: clear in case we were pasting this and it's set somehow
    arcpy.env.outputCoordinateSystem = None
    national_reclassify = calc("national", lambda _: arcpy.gp.Reclassify_sa(Raster(national), "Value", ';'.join(["{} {}".format(k, v) for k, v in dct_2018.iteritems()]), _, "DATA"))
    MIN_LAT = common.BOUNDS['latitude']['min']
    MAX_LAT = common.BOUNDS['latitude']['max']
    MIN_LON = common.BOUNDS['longitude']['min']
    MAX_LON = common.BOUNDS['longitude']['max']
    bounds_array = arcpy.Array([arcpy.Point(MIN_LON, MAX_LAT),
                                arcpy.Point(MIN_LON, MIN_LAT),
                                arcpy.Point(MAX_LON, MIN_LAT),
                                arcpy.Point(MAX_LON, MAX_LAT)])
    # trying to just use NAD83 (4269) didn't work (made a 1x1 raster for some reason)
    # MNR Lambert Conformal Conic (3161) doesn't seem to work (not lat/long?)
    # WGS 84 (4326) should let us define things in lat/lon
    PROJ = arcpy.SpatialReference(4326)
    bounds_polygon = arcpy.Polygon(bounds_array, PROJ)
    # /1
    env_pop()
    gridSize = CELLSIZE_M
    bigGridSize_km = 50
    bigGridSize_m = bigGridSize_km * 1000
    make_grid(ZONES)
    # \1
    bounds_grids = checkGDB(BOUNDS_DIR, "bounds_{:03d}m.gdb".format(CELLSIZE_M))
    env_push()
    env_defaults(workspace=bounds_grids,
                 cellSize=CELLSIZE_M)
    boundBox = check_make("BoundBox", lambda _: arcpy.MinimumBoundingGeometry_management(bounds_polygon, _, "ENVELOPE"))
    roundBound = check_make("RoundBound", lambda _: arcpy.Buffer_analysis(boundBox, _, BUFF_DIST))
    # HACK: don't want rounded corners so do this again.
    bounds = check_make("bounds", lambda _: arcpy.MinimumBoundingGeometry_management(roundBound, _, "ENVELOPE"))
    # project to MNR Lambert so that buffer works in meters
    bounds_project = project(bounds, "bounds_project")
    buffer = check_make("buffer", lambda _: arcpy.FeatureToRaster_conversion(bounds_project, arcpy.ListFields(bounds_project)[0].name, _, CELLSIZE_M))
    # NOTE: make sure [bounds] is first so it uses projection from it
    all_bounds = check_make("AllBounds", lambda _: arcpy.Merge_management(';'.join([bounds_project] + map(lambda x: os.path.join(BOUNDS_DIR, "zone_{}".format(x).replace(".", "_"), "grids_{}m.gdb".format(CELLSIZE_M), "ZoneBuffer"), ZONES)), _))
    DEM_BOX = check_make("box", lambda _: arcpy.MinimumBoundingGeometry_management(all_bounds, _, "ENVELOPE", "ALL"))
    # \2
    env_push()
    env_defaults(snapRaster=buffer, cellSize="")
    DEM_clip = calc("DEM_clip", lambda _: clip_raster_box(EARTHENV, DEM_BOX, _), buildPyramids=False)
    DEM_project = calc("DEM_project", lambda _: project_raster(DEM_clip, _, cellsize_m=CELLSIZE_M, resampling_type="BILINEAR"))
    all_buffer = check_make("all_buffer", lambda _: arcpy.FeatureToRaster_conversion(DEM_BOX, arcpy.ListFields(DEM_BOX)[0].name, _, CELLSIZE_M))
    # /2
    env_pop()
    # \2
    env_push()
    env_defaults(mask=all_buffer, extent=all_buffer, snapRaster=all_buffer, cellSize="")
    # make a mask of what's in the country
    # make bounds for use in erasing from NHD data
    can_clip = check_make("canada_clip", lambda _: arcpy.Clip_analysis(canada, DEM_BOX, _))
    canada_project = project(can_clip, "canada_project")
    canada_box = check_make("canada_box", lambda _: arcpy.Clip_analysis(canada_project, DEM_BOX, _))
    canada_raster = check_make("canada_raster", lambda _: arcpy.FeatureToRaster_conversion(canada_box, "OBJECTID", _, CELLSIZE_M))
    # \3
    env_push()
    env_defaults(workspace=checkGDB(WATER_DIR, "water.gdb"))
    water_projected = checkGDB(WATER_DIR, "water_projected.gdb")
    def check_water(_):
        # \4
        water_list = (map(lambda _: makeWater(_, water_projected), ['ON', 'MB', 'NU', 'NS', 'NB', 'QC']) +
                     [makeWater('US', water_projected, can_box, orig=lakes_nhd, clear=True, sql="FTYPE NOT IN ( 361, 378, 466 )", clip=DEM_BOX),
                      makeWater('USArea', water_projected, can_box, orig=lakes_nhd_area)])
        water_ALL = check_make("water_ALL", lambda _: arcpy.Merge_management(";".join(water_list), _))
        def makeWaterFinal(_):
            arcpy.Sort_management(water_ALL, _, [["Shape", "ASCENDING"]])
            arcpy.AddField_management(_, "gridcode", "SHORT")
            arcpy.CalculateField_management(_, "gridcode", "102", "PYTHON")
        return check_make(_, makeWaterFinal)
    WATER = check_make(os.path.join(water_projected, "water"), check_water)
    # /3
    env_pop()
    fuels = map(create_fuel, ZONES)
    # /2
    env_pop()
    # /1
    env_pop()
    print("Done")
