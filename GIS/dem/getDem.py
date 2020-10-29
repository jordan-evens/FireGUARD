from config import CONFIG
import log
import logging

import os

from merge import to_mosaic
from unpack import check_tar
from util import save_http

def getDEM(force=False):
    """Find DEM files"""
    if not force and os.path.exists(CONFIG["BASE_DEM"]):
        logging.debug("Already have {}".format(CONFIG["BASE_DEM"]))
        return
    logging.info("Collecting for {}".format(CONFIG["BASE_DEM"]))
    # leave these out of config because they're so closely tied to getting the EarthEnv DEM layer
    FROM_DIR = CONFIG["DEM_URL"]
    # also available at this URL but can't auto-download
    # http://datacommons.cyverse.org/browse/iplant/home/shared/earthenv_dem_data/EarthEnv-DEM90_Metadata.csv
    METADATA = r'EarthEnv-DEM90_Metadata.csv'
    FILE_MASK = 'EarthEnv-DEM90_N{:02d}W{:03d}.tar.gz'
    to_dir = CONFIG["DEM_FTP"]
    save_http(to_dir, FROM_DIR + '/' + METADATA, ignore_existing=True)
    for latitude in CONFIG["DEM_LATITUDES"]:
        for longitude in CONFIG["DEM_LONGITUDES"]:
            file = FILE_MASK.format(latitude, longitude)
            save_http(to_dir, FROM_DIR + '/' + file, ignore_existing=True)
    # http://mirrors.iplantcollaborative.org/earthenv_dem_data/EarthEnv-DEM90/
    check_tar(CONFIG["DEM_FTP"], '*', output=CONFIG["DEM_FOLDER"], force=force)
    to_mosaic(CONFIG["DEM_FOLDER"], CONFIG["BASE_DEM"], mask="*.bil", force=force)


if __name__ == "__main__":
    getDEM()
