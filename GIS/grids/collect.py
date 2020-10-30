from shared import download
from shared import unzip
import certifi
import ssl
import os


## So HTTPS transfers work properly
ssl._create_default_https_context = ssl._create_unverified_context

canada = r'http://www12.statcan.gc.ca/census-recensement/2011/geo/bound-limit/files-fichiers/lcsd000a19a_e.zip'

fbp = r'https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/Canadian_Forest_FBP_Fuel_Types_v20191114.zip'
if not os.path.exists('extracted'):
    os.mkdir('extracted')
unzip(download(canada, 'download'), r'extracted\canada')
unzip(download(fbp, 'download'), r'extracted\fbp')

