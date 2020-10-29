"""Handles configuration for all scripts"""
from ConfigParser import ConfigParser
import os
import sys
from urlparse import urlparse
import StringIO
import re

# File listing values to use for various options
ROOT = "C:\\FireGuard\\GIS"
CONFIG_FILE = os.path.join(ROOT, "dem", "config.ini")

def read_config(file_name):
    # HACK: put special sequence at end so that we can replace it later
    COMMENT_GUARD = '^@_@'
    """Set options; if there is an error use the defaults"""
    config = ConfigParser(allow_no_value=True)
    # set options this way so we can comment them
    def value(option, value=None, section="DEFAULT"):
        """Set a default value in section of the config"""
        config.set(section, option, value)
    def note(value, section="DEFAULT"):
        """Add a note in section of the config"""
        config.set(section, "# " + value + COMMENT_GUARD)
    # [DEFAULT]
    note("'%(var)s' syntax means it will be replaced with value of that variable")
    note("Logging level")
    value("LOG_LEVEL", "DEBUG")
    note("Root directory")
    value("ROOT", ROOT)
    note("Source directory")
    value("SOURCE", "%(root)s\\hg")
    note("Data directory")
    value("DATA", "%(root)s\\data")
    note("Extracted files directory")
    value("EXTRACTED", "%(data)s\\extracted")
    note("Intermediate files directory - don't want to clutter final gdb but want to keep intermediate calculation")
    value("INTERMEDIATE", "%(data)s\\intermediate")
    note("FTP download directory")
    value("FTP", "%(root)s\\ftp")
    # this is in a separate folder to make robocopy easier
    note("Where to store base GIS data")
    value("GIS_BASE", "%(data)s\\base")
    note("GDB that files are collected into")
    value("COLLECTED.GDB", "%(gis_base)s\\collected.gdb")
    note("Buffer size to use for clipping to each study area")
    value("BUFFER_KM", "15")
    note("Cell size to use for generated rasters")
    value("DEFAULT_CELLSIZE_M", "500")
    note("Cell buffer percent to use for WindNinja and other cells")
    value("CELL_BUFFER_PCT", "20")
    note("Distance to use for Topographic Position Index")
    value("TPI_DISTANCE", "3000")
    note("Units to use for Topographic Position Index distance (options are CELL or MAP)")
    value("TPI_UNITS", "MAP")
    note("Default size to use for fishnet for WindNinja calculation")
    value("GRIDSIZE_KM", "100")
    note("Location of WindNinja binary to call")
    value("WINDNINJA.EXE", r'C:\WindNinja\WindNinja-3.1.0\bin\WindNinja_cli.exe')
    note("WindNinja config to use for default parameters")
    value("WINDNINJA_CONFIG", "%(source)s\\windninja.cfg")
    note("Grid size to use for windninja input - separate from DEFAULT_CELLSIZE_M, and should be the same size or smaller")
    value("WINDNINJA_INPUT_CELLSIZE_M", "100")
    note("Default projection")
    value("PROJECTION", "PROJCS['Canada_Lambert_Conformal_Conic',GEOGCS['GCS_North_American_1983',DATUM['D_North_American_1983',SPHEROID['GRS_1980',6378137.0,298.257222101]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Lambert_Conformal_Conic'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',-96.0],PARAMETER['Standard_Parallel_1',50.0],PARAMETER['Standard_Parallel_2',70.0],PARAMETER['Latitude_Of_Origin',40.0],UNIT['Meter',1.0]]")
    note("Location of shared drive shapefiles")
    value("SHARED_SHAPEFILES", "%(fire-cc)s\\VolFCC02\\shapefiles")
    note("Location of shared drive datasets")
    value("SHARED_DATASETS", "%(fire-cc)s\\VolFCC02\\datasets")
    # [CANVEC]
    config.add_section("CANVEC")
    note("Resolution of CANVEC data to use", "CANVEC")
    value("CANVEC_RESOLUTION", "50K", "CANVEC")
    note("Folder to download CANVEC data from", "CANVEC")
    value("CANVEC_URL", r'ftp://ftp.geogratis.gc.ca/pub/nrcan_rncan/vector/canvec/', "CANVEC")
    note("File mask to use for matching canvec resolution, theme, and feature", "CANVEC")
    value("CANVEC_MASK", "canvec_{resolution}_{province}_{theme}", "CANVEC")
    note("Distance to use for Kernel Density tool (m)", "CANVEC")
    value("CANVEC_KERNEL_DISTANCE", "25000", "CANVEC")
    # [FIRES]
    config.add_section("FIRES")
    note("URL to download fire point data from", "FIRES")
    value("FIRES_URL", r'ftp://ftp.nofc.cfs.nrcan.gc.ca/pub/fire/nfdb/fire_pnt/current_version/NFDB_point.zip', "FIRES")
    note("Root file name for fires data", "FIRES")
    value("FIRES_ROOT", "NFDB_point_", "FIRES")
    note("Date for fires data to use", "FIRES")
    value("FIRES_DATE", "20161202", "FIRES")
    note("Base file name that all files for fire data will share", "FIRES")
    value("FIRES_BASE",  "%(fires_root)s%(fires_date)s", "FIRES")
    note("Fires shapefile name (since it doesn't match zip name", "FIRES")
    value("FIRES", "%(fires_base)s.shp", "FIRES")
    note("URL to download fires metadata from", "FIRES")
    value("FIRES_METADATA_URL", r'ftp://ftp.nofc.cfs.nrcan.gc.ca/pub/fire/nfdb/fire_pnt/current_version/%(fires_base)s_metadata.pdf', "FIRES")
    note("URL to download fires documentation from", "FIRES")
    value("FIRES_DOCUMENTATION_URL", r'ftp://ftp.nofc.cfs.nrcan.gc.ca/pub/fire/nfdb/fire_pnt/current_version/NFDB_BNDFFC_documentation.pdf', "FIRES")
    # [DEM]
    config.add_section("DEM")
    note("Directory to download DEM files from", "DEM")
    value("DEM_URL", r'http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/', "DEM")
    # [FUELS]
    config.add_section("FUELS")
    note("URL to download fuels FBP fuels layer to use", "FUELS")
    value("FUELS_URL", r'http://cwfis.cfs.nrcan.gc.ca/downloads/fuels/nat_fbpfuels_2014b.zip', "FUELS")
    note("URL to download fuels metadata from", "FUELS")
    value("FUELS_METADATA_URL", r'http://cwfis.cfs.nrcan.gc.ca/downloads/fuels/nat_pub_2014b_metadata.pdf', "FUELS")
    # [SHAPEFILES]
    config.add_section("SHAPEFILES")
    note("NOTE: all items in this section will be collected into collected.gdb", "SHAPEFILES")
    note("Feature to use for determining extent of area of concern", "SHAPEFILES")
    value("BOUNDARIES", "%(fire-cc)s\\VolFCC01\\Projects\\largeFiresCanada\\1. DataFromJohn\\REDCAP_FMW_20000kha.shp", "SHAPEFILES")
    note("Provinces admin boundaries", "SHAPEFILES")
    value("PROVINCE_BOUNDARIES", "%(shared_shapefiles)s\\CanadianAdminBoundaries\\CAN_adm1.shp", "SHAPEFILES")
    # [RASTERS]
    config.add_section("RASTERS")
    note("NOTE: all items in this section will be collected into collected.gdb", "RASTERS")
    # HACK: really only need a list of province short forms, but do this as a section so we can use get_list()
    # [PROVINCES]
    config.add_section("PROVINCES")
    note("short forms for provinces that are used in file names", "PROVINCES")
    if os.path.exists(file_name):
        config.read(file_name)
    else:
        # only required for default values of keys, so don't include if removed
        note("Set to value of where \\\\s2-ssm-r2007\\Fire-CC\\ is mapped")
        value("FIRE-CC", "Z:")
        # unused items, but just for convenience in visualizing if in arcmap
        note("250k topographic index sheet", "SHAPEFILES")
        value("UNUSED_TOPO_250K", "%(shared_datasets)s\\National_Topographic_IndexSheets\\decoupage_snrc250k_2.shp", "SHAPEFILES")
        note("50k topographic index sheet", "SHAPEFILES")
        value("UNUSED_TOPO_50K", "%(shared_datasets)s\\National_Topographic_IndexSheets\\decoupage_snrc50k_2.shp", "SHAPEFILES")
        # unused items, but just for convenience in visualizing if in arcmap
        note("old fbp fuels layer", "RASTERS")
        value("UNUSED_FUELS", "%(shared_datasets)s\\Fuels Maps\\National Fuels Basemap\\v4\\cwfis_2013", "RASTERS")
        # add in values that we don't want to keep defaulting to if config is edited
        value("Alberta", "AB", "PROVINCES")
        value("British Columbia", "BC", "PROVINCES")
        value("Manitoba", "MB", "PROVINCES")
        value("New Brunswick", "NB", "PROVINCES")
        value("Newfoundland", "NL", "PROVINCES")
        value("Nova Scotia", "NS", "PROVINCES")
        value("Northwest Territories", "NT", "PROVINCES")
        value("Nunavat", "NU", "PROVINCES")
        value("Ontario", "ON", "PROVINCES")
        value("Prince Edward Island", "PE", "PROVINCES")
        value("Quebec", "QC", "PROVINCES")
        value("Saskatchewan", "SK", "PROVINCES")
        value("Yukon", "YT", "PROVINCES")
        
        # HACK: write out the config right away so it's got defaults and everything
        # HACK: go through output first to get rid of ' = None' at end of comments in DEFAULT section
        fakefile = StringIO.StringIO()
        config.write(fakefile)
        with open(file_name, "w") as out:
            for line in fakefile.getvalue().split('\n'):
                # HACK: need to replace two different things since DEFAULT section ends up with ' = None'
                out.write(line.replace(COMMENT_GUARD + " = None", "").replace(COMMENT_GUARD, "") + '\n')
        fakefile.close()
    def get_int(option, section="DEFAULT"):
        """Get an int from a section of the config"""
        return config.getint(section, option)
    def get_float(option, section="DEFAULT"):
        """Get a float from a section of the config"""
        return config.getfloat(section, option)
    def get_boolean(option, section="DEFAULT"):
        """Get a boolean from a section of the config"""
        return config.getboolean(section, option)
    def get(option, section="DEFAULT"):
        """Get a string from a section of the config"""
        return config.get(section, option)
    def get_list(section):
        """Get a list of all non-null values in the section"""
        # HACK: items() returns all defaults too, so ignore those
        defaults = [key for key, value in config.items("DEFAULT")]
        return [value for key, value in config.items(section) if (value and key not in defaults)]
    def get_gdbs():
        """Get a list of all keys that are for .gdbs"""
        # HACK: items() returns all defaults too, so ignore those
        return [key.upper() for key, value in config.items("DEFAULT") if key.upper().endswith(".GDB") and  "{}" not in value]
    def fix_name(name):
        """Find first group of alphanumeric characters and use that"""
        return re.match('[A-Za-z0-9_]*', name).group(0)
    def get_feature_name(option, section="DEFAULT"):
        basename = os.path.basename(get(option, section))
        if not basename:
            # option ends in a directory with a / so use that name
            basename = os.path.basename(os.path.dirname(get(option, section)))
        return fix_name(os.path.splitext(basename)[0])
    def get_ftp(option, section="DEFAULT"):
        """Return the path to the where the feature should be downloaded locally"""
        u = urlparse(get(option, section))
        # HACK: split so that '/' gets replaced by proper os folder character
        return os.path.join(get("FTP"), *(os.path.dirname(u.netloc + u.path).split('/')))
    def get_unpack_folder(option, section="DEFAULT"):
        """Return path to where to unpack data for feature"""
        return os.path.join(get("EXTRACTED"), get_feature_name(option, section))
    def get_collected(option, section="DEFAULT", gdb="COLLECTED.GDB"):
        """Return the path to the feature after it has been collected and stored locally"""
        return os.path.join(get(gdb), get_feature_name(option, section))
    # HACK: make these specifically here so they're hidden from the config
    # final unprojected outputs
    value("UNPROJECTED.GDB", os.path.join("%(intermediate)s", "unprojected.gdb"))
    # final derived outputs in correct projection
    value("DERIVED.GDB", os.path.join("%(data)s", "derived.gdb"))
    # intermediate files that we don't want to recalculate but don't need to see
    value("INTERMEDIATE.GDB", os.path.join("%(intermediate)s", "intermediate.gdb"))
    # HACK: do this after we write because we want to hide this but use it so each cellsize has its own gdb
    value("DERIVEDGRIDMASK.GDB", os.path.join("%(data)s", "derived{}m.gdb"))
    value("INTERMEDIATEGRIDMASK.GDB", os.path.join("%(intermediate)s", "intermediate{}m.gdb"))
    # HACK: we rely on knowing that the windninja grid is going to be in a specific gdb
    value("WINDNINJA.GDB", "%(data)s/derived{}m.gdb".format(get_int("WINDNINJA_INPUT_CELLSIZE_M")))
    # HACK: don't return the ConfigParser because we only want these values
    # HACK: override with local variable so we can use same name
    CONFIG = {
        "LOG_LEVEL": get("LOG_LEVEL"),
        "PROJECTION": get("PROJECTION"),
        "ROOT": get("ROOT"),
        "BUFFER_KM": get_int("BUFFER_KM"),
        "DEFAULT_CELLSIZE_M": get_int("DEFAULT_CELLSIZE_M"),
        # HACK: access as a ratio but base off a percent so it can't be < 1
        "CELL_BUFFER_RATIO": 1.0 + (get_int("CELL_BUFFER_PCT") / 100.0),
        "TPI_DISTANCE": get_int("TPI_DISTANCE"),
        "TPI_UNITS": get("TPI_UNITS"),
        "GRIDSIZE_KM": get_int("GRIDSIZE_KM"),
        "FTP": get("FTP"),
        "FUELS_FTP": get_ftp("FUELS_URL", "FUELS"),
        "FUELS_URL": get("FUELS_URL", "FUELS"),
        "FUELS_METADATA_URL": get("FUELS_METADATA_URL", "FUELS"),
        "FUELS": get_feature_name("FUELS_URL", "FUELS"),
        "FUELS_FOLDER": get_unpack_folder("FUELS_URL", "FUELS"),
        "DATA": get("DATA"),
        "INTERMEDIATE": get("INTERMEDIATE"),
        "EXTRACTED": get("EXTRACTED"),
        "SOURCE": get("SOURCE"),
        "GIS_BASE": get("GIS_BASE"),
        "COLLECTED.GDB": get("COLLECTED.GDB"),
        "COLLECT_SHAPEFILES": get_list("SHAPEFILES"),
        "COLLECT_RASTERS": get_list("RASTERS"),
        "INTERMEDIATE.GDB": get("INTERMEDIATE.GDB"),
        "UNPROJECTED.GDB": get("UNPROJECTED.GDB"),
        "DERIVED.GDB": get("DERIVED.GDB"),
        "INTERMEDIATEGRIDMASK.GDB": get("INTERMEDIATEGRIDMASK.GDB"),
        "DERIVEDGRIDMASK.GDB": get("DERIVEDGRIDMASK.GDB"),
        "WINDNINJA.GDB": get("WINDNINJA.GDB"),
        "GDBS": get_gdbs(),
        "WINDNINJA_INPUT_CELLSIZE_M": get_int("WINDNINJA_INPUT_CELLSIZE_M"),
        "DEM_WINDNINJA": get_collected("DEM_URL", "DEM", gdb="WINDNINJA.GDB"),
        "WINDNINJA.EXE": get("WINDNINJA.EXE"),
        "WINDNINJA_CONFIG": get("WINDNINJA_CONFIG"),
        "BOUNDARIES": get("BOUNDARIES", "SHAPEFILES"),
        "BASE_BOUNDS": get_collected("BOUNDARIES", "SHAPEFILES"),
        "DEM": get_feature_name("DEM_URL", "DEM"),
        "DEM_FTP": get_ftp("DEM_URL", "DEM"),
        "DEM_URL": get("DEM_URL", "DEM"),
        "DEM_FOLDER": get_unpack_folder("DEM_URL", "DEM"),
        # HACK: having serious issues with trying to mosaic this into a gdb, so use a tif
        "BASE_DEM": os.path.join(get("INTERMEDIATE"), get_feature_name("DEM_URL", "DEM") + ".tif"),
        "BASE_FUELS": get_collected("FUELS_URL", "FUELS"),
        "BASE_FIRES": get_collected("FIRES", "FIRES"),
        "FIRES_PROJ": get_collected("FIRES", "FIRES", "DERIVED.GDB"),
        "BOUNDS_PROJ": get_collected("BOUNDARIES", "SHAPEFILES", "DERIVED.GDB"),
        "PROVINCES": get_list("PROVINCES"),
        "CANVEC_RESOLUTION": get("CANVEC_RESOLUTION", "CANVEC"),
        "CANVEC_FTP": get_ftp("CANVEC_URL", "CANVEC"),
        "CANVEC_URL": get("CANVEC_URL", "CANVEC"),
        "CANVEC_FOLDER": get_unpack_folder("CANVEC_URL", "CANVEC"),
        "CANVEC_MASK": get("CANVEC_MASK", "CANVEC"),
        "CANVEC_KERNEL_DISTANCE": get_int("CANVEC_KERNEL_DISTANCE", "CANVEC"),
        "FIRES_URL": get("FIRES_URL", "FIRES"),
        "FIRES_DOCUMENTATION_URL": get("FIRES_DOCUMENTATION_URL", "FIRES"),
        "FIRES_METADATA_URL": get("FIRES_METADATA_URL", "FIRES"),
        "FIRES_FTP": get_ftp("FIRES_URL", "FIRES"),
        "FIRES": get("FIRES", "FIRES"),
        "FIRES_BASE": get("FIRES_BASE", "FIRES"),
        "FIRES_FOLDER": get_unpack_folder("FIRES_URL", "FIRES"),
        "PROVINCE_BOUNDARIES": get_collected("PROVINCE_BOUNDARIES", "SHAPEFILES"),
        # HACK: don't have anything to do with config file, but put here so accessible
        # seems like it would be messy to try to ensure that user-set # of degrees always
        # works nicely and prometheus expects these directions
        "WIND_DIRECTIONS": xrange(0, 360, 45),
        "WIND_SPEEDS": [10],
        # know these are correct for Canada and EarthEnv-DEM90, but set them here to keep track of them
        "DEM_LATITUDES": xrange(35, 85, 5),
        "DEM_LONGITUDES": xrange(45, 160, 5),
    }
    # HACK: do this so ArcMap imports actually work after this file is loaded
    if CONFIG["SOURCE"] not in sys.path:
        sys.path.append(CONFIG["SOURCE"])
    return CONFIG

CONFIG = read_config(CONFIG_FILE)

if __name__ == "__main__":
    for key, value in sorted(CONFIG.iteritems()):
        print key
        print " " + str(value)

