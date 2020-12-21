from shared import download
from shared import unzip
import certifi
import ssl
import os


## So HTTPS transfers work properly
ssl._create_default_https_context = ssl._create_unverified_context

DATA_DIR = os.path.realpath('/FireGUARD/data')
EXTRACTED_DIR = os.path.join(DATA_DIR, 'extracted')
DOWNLOAD_DIR = os.path.join(DATA_DIR, 'download')
canada = r'http://www12.statcan.gc.ca/census-recensement/2011/geo/bound-limit/files-fichiers/lcsd000a19a_e.zip'

fbp = r'https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/Canadian_Forest_FBP_Fuel_Types_v20191114.zip'
if not os.path.exists(EXTRACTED_DIR):
    os.makedirs(EXTRACTED_DIR)
unzip(download(canada, DOWNLOAD_DIR), os.path.join(EXTRACTED_DIR, r'canada'))
unzip(download(fbp, DOWNLOAD_DIR), os.path.join(EXTRACTED_DIR, r'fbp'))

