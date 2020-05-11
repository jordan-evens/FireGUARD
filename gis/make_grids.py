import shapefile

from Settings import Settings

settings = Settings()

ZONE_MIN = 15 + (settings.longitude_min + 93.0) / 6.0
if int(ZONE_MIN) < ZONE_MIN:
    ZONE_MIN = int(ZONE_MIN) + 0.5
ZONE_MAX = 15 + (settings.longitude_max + 93.0) / 6.0
if int(ZONE_MAX) < ZONE_MAX:
    ZONE_MAX = int(ZONE_MAX) + 0.5

zone = ZONE_MIN
while zone <= ZONE_MAX:
    zone_fmt = '{}'.format(zone).replace('.', '_')
    shp = 'utm_{}'.format(zone_fmt)
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
    zone += 0.5


