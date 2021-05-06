from config import CONFIG
import log
import logging

from util import save_ftp
from util import save_http
import ftplib
import zipfile
import os
import sys
from unpack import check_zip

THEMES_ADMIN = ["Admin"]
THEMES_250K_50K = ["ManMade", "Res_MGT"]
THEMES_MAIN = ["Elevation", "Hydro", "Land", "Transport"]
THEMES_50K_ONLY = ["Toponymy"]
THEMES = THEMES_ADMIN + THEMES_250K_50K + THEMES_MAIN + THEMES_50K_ONLY

def ensure_canvec(theme, prov, extract=True, resolution='50K'):
    """Make sure we have the proper gdb downloaded and unzipped"""
    if theme not in THEMES:
        return None
    gdb_root = CONFIG["CANVEC_MASK"].format(resolution=resolution, province=prov, theme=theme)
    gdb = gdb_root + ".gdb"
    path = os.path.join(CONFIG["CANVEC_FOLDER"], gdb)
    logging.debug("Looking for {}".format(path))
    # if we're only trying to download them then don't check if unzipped, just do download checks
    if extract and os.path.exists(path):
        return path
    zipname = gdb_root + "_fgdb.zip"
    dir_base =  os.path.join("fgdb", theme)
    remote_dir = os.path.join(CONFIG["CANVEC_URL"], dir_base.replace('\\', '/'))
    local_dir = os.path.join(CONFIG["CANVEC_FTP"], dir_base)
    remote_file = os.path.join(remote_dir, zipname).replace('\\', '/')
    local_file =  os.path.join(local_dir, zipname)
    corrupt = False
    if os.path.exists(local_file):
        try:
            # HACK: use not not to force it into a boolean value
            corrupt = not not zipfile.ZipFile(local_file).testzip()
        except zipfile.BadZipfile:
            corrupt = True
    if corrupt:
        logging.error("Removing corrupt zip file {}".format(local_file))
        os.remove(local_file)
    if not os.path.exists(local_file):
        logging.debug("Need to download {}".format(remote_file))
        save_http(local_dir, remote_file, ignore_existing=True)
    if extract:
        # have this parameter so we can download everything without extracting it
        check_zip(CONFIG["CANVEC_FTP"], "*{}*".format(gdb_root), file_mask=zipname, output=CONFIG["CANVEC_FOLDER"], force=True)
    return path if os.path.exists(path) else None

def download_all(extract=False):
    """Ensures that all canvec data for current resolution is downloaded"""
    for theme in THEMES_ADMIN:
        for resolution in ["1M"]:
            ensure_canvec(theme, "CA", extract, resolution)
    for theme in THEMES_250K_50K:
        for resolution in ["250K", "50K"]:
            for prov in CONFIG["PROVINCES"]:
                ensure_canvec(theme, prov, extract, resolution)
            ensure_canvec(theme, "CA", extract, resolution)
    for theme in THEMES_MAIN:
        for prov in CONFIG["PROVINCES"]:
            for resolution in ["250K", "50K"]:
                ensure_canvec(theme, prov, extract, resolution)
        # download Canada gdbs
        for resolution in ["15M", "5M", "1M"]:
                ensure_canvec(theme, "CA", extract, resolution)
    for theme in THEMES_50K_ONLY:
        for resolution in ["50K"]:
            for prov in CONFIG["PROVINCES"]:
                ensure_canvec(theme, prov, extract, resolution)
            ensure_canvec(theme, "CA", extract, resolution)

if __name__ == "__main__":
    # parse requested themes and only do those
    if len(sys.argv) >= 3:
        requested = sys.argv[2:]
        themes = []
        for t in requested:
            if t.upper() not in map(lambda x: x.upper(), THEMES):
                logging.fatal("Theme '{}' does not exist".format(t))
                sys.exit(-1)
            # HACK: find proper casing by looping again for now
            for c in THEMES:
                if c.upper() == t.upper():
                    themes.append(c)
        THEMES = themes
    # has to have started with one of the options
    if len(sys.argv) >= 2 and sys.argv[1] == 'download':
        download_all()
    elif len(sys.argv) >= 2 and sys.argv[1] == 'extract':
        download_all(True)
    else:
        logging.critical("Invalid arguments.  Expected:\n{ps} [download|extract] <THEMES>".format(ps=sys.argv[0]))
        sys.exit(-1)
