"""Helper functions used by multiple files"""
from config import CONFIG
import log
import logging

# import arcpy
import os
from util import ensure_dir
from util import find_files
import math

import rasterio
from rasterio.merge import merge
from rasterio.plot import show
import glob

ENVIRONMENTS = []


def env_push():
    """Push all environment variables so we can revert easily"""
    env = {}
    for key in arcpy.env:
        env[key] = arcpy.env[key]
    ENVIRONMENTS.append(env)

def env_pop():
    """Revert to last settings for all environment variables"""
    # no error check so that we know if we did things wrong
    env = ENVIRONMENTS.pop()
    for key in env:
        try:
            arcpy.env[key] = env[key]
        except:
            # must be a read-only property, so no way we changed it and don't need to revert
            pass


def to_gdb(folder, mask, gdb, input_folder, output_folder, fct):
    """Apply function to matching files after creating gdb"""
    logging.debug("Adding items from folder '" + folder + "'")
    if not gdb:
        gdb = folder + '.gdb'
    input = os.path.join(input_folder, folder)
    gdb_path = tryCreateFileGDB(output_folder, gdb)
    files = find_files(input, mask)
    if 0 == len(files):
        logging.debug("No files found")
        return
    fct(gdb_path, files)


def raster_to_gdb(folder, mask='*.tif', gdb=None, input_folder=CONFIG["EXTRACTED"], output_folder=CONFIG["DATA"]):
    """Load matching rasters into gdb"""
    to_gdb(folder, mask, gdb, input_folder, output_folder, tryRasterToGeodatabase)


def feature_to_gdb(folder, mask='*.shp', gdb=None, input_folder=CONFIG["EXTRACTED"], output_folder=CONFIG["DATA"]):
    """Load matching features into gdb"""
    to_gdb(folder, mask, gdb, input_folder, output_folder, tryFeatureClassToGeodatabase)


def to_mosaic(input, output_file, projection=None, mask=None, output_workspace=None, pixelType=None, force=False):
    """Mosaic matching rasters together"""
    logging.debug("Adding rasters from '" + input + "'")
    if not output_workspace:
        output_workspace = os.path.dirname(output_file)
        output_file = os.path.basename(output_file)
    path = os.path.join(output_workspace, output_file)
    # do this check right now so we have proper output name for check existing
    if not output_workspace.lower().endswith(".gdb") and "." not in output_file:
        # add .tif extension if none supplied
        logging.debug("Defaulting to TIF format")
        output_file = output_file + ".tif"
    if not force and os.path.exists(path):
        logging.debug("Mosaic {} already exists".format(path))
        return
    files = None
    if mask == None:
        mask = '*.tif'
    files = find_files(input, mask)
    files = map(lambda x: os.path.relpath(x, input), files)
    if 0 == len(files):
        logging.debug("No files found")
        return
    src_files_to_mosaic = []
    for fp in files:
        src = rasterio.open(os.path.join(input, fp))
        src_files_to_mosaic.append(src)
    mosaic, out_trans = merge(src_files_to_mosaic)
    out_meta = src.meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": mosaic.shape[1],
                     "width": mosaic.shape[2],
                     "transform": out_trans,
                     "crs": "+proj=utm +zone=35 +ellps=GRS80 +units=m +no_defs "
                     }
                    )
    with rasterio.open(out_fp, "w", **out_meta) as dest:
        dest.write(mosaic)
    

def setSnapAndExtent(feature):
    """Set snapRaster and extent to match feature"""
    arcpy.env.snapRaster = feature
    arcpy.env.extent = feature

def env_defaults(
            snapAndExtent=None,
            pyramid="PYRAMIDS -1 NEAREST DEFAULT 75 NO_SKIP",
            overwriteOutput=1,
            addOutputsToMap=False,
            workspace=None
    ):
    """Set default settings for environment"""
    arcpy.env.pyramid = pyramid
    if snapAndExtent and arcpy.Exists(snapAndExtent):
        setSnapAndExtent(snapAndExtent)
    # Just overwrite all outputs instead of worrying about deleting them properly first
    arcpy.env.overwriteOutput = overwriteOutput
    # stop adding everything to the map
    arcpy.env.addOutputsToMap = addOutputsToMap
    # default to using current workspace but have parameter so we can override
    if workspace:
        arcpy.env.workspace = workspace


def find_transformation(spatialReference, projection):
    """Figure out a valid transformation from the spatialReference to the desired one"""
    projectedReference = arcpy.SpatialReference()
    projectedReference.loadFromString(projection)
    # don't use extent because this gives the same first option as picking in Project Raster tool
    list = arcpy.ListTransformations(spatialReference, projectedReference)
    # if no transformations then assum that this means no transformation required
    return list[0] if len(list) > 0 else ""


def project_raster(in_raster, out_raster, cellsize_m, resampling_type=""):
    """Project a raster into the default coordinate system with the proper cell size and reference point"""
    cell_size = "{} {}".format(cellsize_m, cellsize_m)
    geographic_transform = find_transformation(arcpy.Describe(in_raster).spatialReference, CONFIG["PROJECTION"])
    arcpy.ProjectRaster_management(in_raster, out_raster, CONFIG["PROJECTION"], resampling_type, cell_size, geographic_transform, "0 0", "")


def project(in_dataset, out_dataset, preserve_shape="", max_deviation="", vertical=""):
    """Project into the default coordinate system"""
    geographic_transform = find_transformation(arcpy.Describe(in_dataset).spatialReference, CONFIG["PROJECTION"])
    arcpy.Project_management(in_dataset, out_dataset, CONFIG["PROJECTION"], geographic_transform, "", preserve_shape, "", vertical)


def tryCreateFileGDB(path, file=None):
    """Create gdb if required and return path to it"""
    # overloaded so we can just give full path or folder + gdb
    if file is None:
        file = os.path.basename(path)
        folder = os.path.dirname(path)
    else:
        folder = path
        path = os.path.join(folder, file)
    if not arcpy.Exists(path):
        logging.info("Creating GDB " + path)
        ensure_dir(folder)
        arcpy.CreateFileGDB_management(folder, file, "CURRENT")
    return path


def check_add(gdb, files, fct):
    """Check if each item is in gdb and call function it if not"""
    paths = []
    for file in files:
        logging.debug("Trying to add {}".format(file))
        basename = os.path.basename(file)
        fc, ext = os.path.splitext(basename)
        # need to do this or else it can't find things with invalid names since they get changed when added
        validated = arcpy.ValidateTableName(fc)
        if not arcpy.Exists(os.path.join(gdb, validated)):
            logging.debug("Adding " + fc + " to " + gdb)
            paths = paths + [file]
        else:
            logging.debug("Ignoring " + fc)
    filelist = ";".join(paths)
    if 0 < len(paths):
        logging.debug(filelist)
        apply(fct, [filelist, gdb])


def tryFeatureClassToGeodatabase(gdb, files):
    """Check if features are in gdb and add it if not"""
    check_add(gdb, files, arcpy.FeatureClassToGeodatabase_conversion)


def tryRasterToGeodatabase(gdb, files):
    """Check if rasters are in gdb and add it if not"""
    check_add(gdb, files, arcpy.RasterToGeodatabase_conversion)

# Derived from https://github.com/NASA-DEVELOP/dnppy/blob/master/dnppy/raster/metadata.py
def get_pixel_type(pt):
    """
    gets a "pixel_type" attribute that matches format of arcpy function
    inputs for manual datatype manipulations from the confusingly encoded
    "pixelType" variable associated with arcpy.Describe()
    as of arcpy 10.2.2
    """
    # determine bit depth
    if "64" in pt:
        return "64_BIT"
    elif "32" in pt:
        bits = 32
    elif "16" in pt:
        bits = 16
    elif "8" in pt:
        bits = 8
    elif "4" in pt:
        return "4_BIT"
    elif "2" in pt:
        return "2_BIT"
    elif "1" in pt:
        return "1_BIT"
    else:
        bits = "0"
    # determine numerical type
    if "U" in pt:
        type = "UNSIGNED"
    elif "S" in pt:
        type = "SIGNED"
    elif "F" in pt:
        type = "FLOAT"
    else:
        type = "UNKNOWN"
    pixel_type = "{0}_BIT_{1}".format(bits, type)
    return pixel_type


def forEachFeature(features, fct):
    """Get result of fct for each feature in features"""
    result = {}
    oid_column = arcpy.Describe(features).OIDFieldName
    shape_column = arcpy.Describe(features).shapeFieldName
    count = int(arcpy.GetCount_management(features).getOutput(0))
    id_length = len(str(count))
    # HACK: do this so that folders all have same number of digits with leading zeros
    id_formatter = "{:0" + str(id_length) + "}"
    # get info for every cell that's in the fishnet
    with arcpy.da.SearchCursor(features, [oid_column, shape_column + '@']) as cursor:
        for row in cursor:
            oid = row[0]
            feat = row[1]
            formatted_id = id_formatter.format(oid)
            result[formatted_id] = fct(formatted_id, feat)
    del row
    del cursor
    return result


def getGridFolder(cellsize_m, feature=""):
    """Figure out which folder to store derived grid files in"""
    # HACK: rely on empty string feature not being joined to get base name
    return ensure_dir(os.path.join(CONFIG["DATA"], "derived{}m".format(cellsize_m), feature))

def getDerivedGrid(cellsize_m, feature=""):
    """Figure out which gdb to store derived grid files in"""
    # HACK: rely on empty string feature not being joined to get base gdb name
    return os.path.join(tryCreateFileGDB(CONFIG["DERIVEDGRIDMASK.GDB"].format(cellsize_m)), feature)


def getIntermediateGrid(cellsize_m, feature=""):
    """Figure out which gdb to store intermediate grid files in"""
    # HACK: rely on empty string feature not being joined to get base gdb name
    return os.path.join(tryCreateFileGDB(CONFIG["INTERMEDIATEGRIDMASK.GDB"].format(cellsize_m)), feature)


def withSpatial(fct):
    """Ensure spatial analyst extension is checked out and call function"""
    # HACK: apparently there's no way to check if extension is already checked out so just check it out
    logging.debug("Checking out extension")
    arcpy.CheckOutExtension("spatial")
    result = fct()
    arcpy.CheckInExtension("spatial")
    return result


def align_grid(gridSize, xMin, yMin, xMax, yMax):
    """
        Want to make sure that no matter what area we're looking at, the grid is always aligned
        so it starts at point (0, 0).  If we do that, it means that windninja and other complicated
        calculations can be reused for cells no matter what area they were generated as part of.
    """
    realXMin = int(math.floor(float(xMin) / gridSize)) * gridSize
    realYMin = int(math.floor(float(yMin) / gridSize)) * gridSize
    realXMax = int(math.ceil(float(xMax) / gridSize)) * gridSize
    realYMax = int(math.ceil(float(yMax) / gridSize)) * gridSize
    return arcpy.Extent(realXMin, realYMin, realXMax, realYMax)


def make_fishnet(area_km, bounds, buffer_km):
    """Create a fishnet for given bounds and select cells that intersect bounds"""
    area_size_m = area_km * 1000
    logging.info("Making {}km fishnet".format(area_km))
    extent = arcpy.Describe(bounds).extent
    # do a rough outline that's 2 extra cells big
    xMax = int((extent.XMax / area_size_m) + 2)  * area_size_m
    xMin = int((extent.XMin / area_size_m) - 2)  * area_size_m
    yMax = int((extent.YMax / area_size_m) + 2)  * area_size_m
    yMin = int((extent.YMin / area_size_m) - 2)  * area_size_m
    width = int((xMax - xMin) / float(area_size_m))
    height = int((yMax - yMin) / float(area_size_m))
    cells = os.path.join(CONFIG["DERIVED.GDB"], "grid{}km{}km{}".format(area_km, buffer_km, os.path.basename(bounds)))
    if arcpy.Exists(cells):
        return cells
    cells_Layer = "cells_Layer"
    # this name is automatically generated by the CreateFishnet_management tool
    aligned = align_grid(area_size_m, xMin, yMin, xMax, yMax)
    arcpy.CreateFishnet_management(cells,
                                   "{} {}".format(aligned.XMin, aligned.YMin),
                                   # for some reason the tool automatically adds 10 to yMin when using ModelBuilder
                                   "{} {}".format(aligned.XMin, aligned.YMin + 10),
                                   "{}".format(area_size_m),
                                   "{}".format(area_size_m),
                                   "0",
                                   "0",
                                   "{} {}".format(aligned.XMax, aligned.YMax),
                                   "NO_LABELS",
                                   "{} {} {} {}".format(aligned.XMin, aligned.YMin, aligned.XMax, aligned.YMax),
                                   "POLYGON")
    # need to define projection or layers are in wrong place
    arcpy.DefineProjection_management(cells, CONFIG["PROJECTION"])
    # need to have feature layers to do selections
    arcpy.MakeFeatureLayer_management(cells, cells_Layer, "", "", "")
    # keep all cells within intersecting area
    arcpy.SelectLayerByLocation_management(cells_Layer, "INTERSECT", bounds, "{} Kilometers".format(buffer_km), "NEW_SELECTION", "INVERT")
    arcpy.DeleteFeatures_management(cells_Layer)
    logging.debug("Done making fishnet")
    return cells


def getExtents(fishnet_cells):
    """Get extent info so we don't need to use the cursor anymore"""
    return forEachFeature(fishnet_cells, lambda _, feat: feat.extent)

