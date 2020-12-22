"""Handles configuration for all scripts"""
from ConfigParser import ConfigParser
import os
import sys
from urlparse import urlparse
import StringIO
import re

# File listing values to use for various options
ROOT = r'C:\FireGUARD\GIS'
CONFIG_FILE = os.path.join(ROOT, "canvec", "config.ini")

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
    value("SOURCE", "%(root)s\\canvec")
    note("Data directory")
    value("DATA", "%(root)s\\..\\data")
    note("Extracted files directory")
    value("EXTRACTED", "%(data)s\\extracted")
    note("Intermediate files directory - don't want to clutter final gdb but want to keep intermediate calculation")
    value("INTERMEDIATE", "%(data)s\\intermediate")
    note("FTP download directory")
    value("FTP", "%(data)s\\download\\ftp")
    # this is in a separate folder to make robocopy easier
    # [CANVEC]
    config.add_section("CANVEC")
    note("Folder to download CANVEC data from", "CANVEC")
    value("CANVEC_URL", r'ftp://ftp.geogratis.gc.ca/pub/nrcan_rncan/vector/canvec/', "CANVEC")
    note("File mask to use for matching canvec resolution, theme, and feature", "CANVEC")
    value("CANVEC_MASK", "canvec_{resolution}_{province}_{theme}", "CANVEC")
    # [PROVINCES]
    config.add_section("PROVINCES")
    note("short forms for provinces that are used in file names", "PROVINCES")
    if os.path.exists(file_name):
        config.read(file_name)
    else:
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
    # HACK: don't return the ConfigParser because we only want these values
    # HACK: override with local variable so we can use same name
    CONFIG = {
        "LOG_LEVEL": get("LOG_LEVEL"),
        "ROOT": get("ROOT"),
        "FTP": get("FTP"),
        "DATA": get("DATA"),
        "INTERMEDIATE": get("INTERMEDIATE"),
        "EXTRACTED": get("EXTRACTED"),
        "SOURCE": get("SOURCE"),
        "PROVINCES": get_list("PROVINCES"),
        "CANVEC_FTP": get_ftp("CANVEC_URL", "CANVEC"),
        "CANVEC_URL": get("CANVEC_URL", "CANVEC"),
        "CANVEC_FOLDER": get_unpack_folder("CANVEC_URL", "CANVEC"),
        "CANVEC_MASK": get("CANVEC_MASK", "CANVEC"),
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

