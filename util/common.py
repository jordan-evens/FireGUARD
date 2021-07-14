"""Shared code"""

import math
import urllib.request as urllib2
import urllib.error
from urllib.parse import urlparse
import dateutil
import time
import dateutil.parser
import datetime
import os
import psycopg2
import psycopg2.extras 
import io
import subprocess
import shlex
import pandas as pd
import logging
import configparser
import re
import numpy as np
import shutil
import certifi
import ssl
import sys
#import pywgrib2_s as wgrib2
import wgrib2
import copy

## So HTTPS transfers work properly
ssl._create_default_https_context = ssl._create_unverified_context

## bounds to use for clipping data
BOUNDS = None

## file to load settings from
SETTINGS_FILE = r'../settings.ini'
## loaded configuration
CONFIG = None

## @cond Doxygen_Suppress
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
## @endcond

# query parameter value required for driver
PARAM = "%s"

def ensure_dir(dir):
    """!
    Check if directory exists and make it if not
    @param dir Directory to ensure existence of
    @return None
    """
    if not os.path.exists(dir):
        os.makedirs(dir)


def read_config(force=False):
    """!
    Read configuration from default file
    @param force Force reading even if already loaded
    @return None
    """
    global CONFIG
    global BOUNDS
    logging.debug('Reading config file {}'.format(SETTINGS_FILE))
    if force or CONFIG is None:
        CONFIG = configparser.SafeConfigParser()
        # set default values and then read to overwrite with whatever is in config
        CONFIG.add_section('FireGUARD')
        # NOTE: should use if this is required to work while proxy isn't already authenticated
        # CONFIG.set('Proxy', 'address', '<user>:<password>@ipv4:port')
        CONFIG.set('FireGUARD', 'proxy', '')
        CONFIG.set('FireGUARD', 'email', '<SUPPORT_EMAIL@DOMAIN.COM>')
        CONFIG.set('FireGUARD', 'active_offer', 'For accessibility accommodations, alternate formats, questions, or feedback, please contact')
        CONFIG.set('FireGUARD', 'fire_root', '')
        CONFIG.set('FireGUARD', 'output_default', '')
        CONFIG.set('FireGUARD', 'perim_archive_root', '')
        CONFIG.set('FireGUARD', 'perim_root', '')
        CONFIG.set('FireGUARD', 'latitude_min', '41')
        CONFIG.set('FireGUARD', 'latitude_max', '58')
        CONFIG.set('FireGUARD', 'longitude_min', '-96')
        CONFIG.set('FireGUARD', 'longitude_max', '-73')
        CONFIG.set('FireGUARD', 'dfoss_connection', '')
        CONFIG.set('FireGUARD', 'url_agency_wx', '')
        CONFIG.set('FireGUARD', 'url_agency_wx_longrange', 'http://www.affes.mnr.gov.on.ca/extranet/Bulletin_Boards/WXProducts/')
        CONFIG.set('FireGUARD', 'fpa_locations_grid', 'longrange.csv')
        CONFIG.set('FireGUARD', 'reanalysis_server', 'ftp://ftp.cdc.noaa.gov/Datasets/ncep.reanalysis/')
        CONFIG.set('FireGUARD', 'reanalysis_server_user', '')
        CONFIG.set('FireGUARD', 'reanalysis_server_password', '')
        CONFIG.set('FireGUARD', 'naefs_server', 'https://nomads.ncep.noaa.gov/cgi-bin/')
        CONFIG.set('FireGUARD', 'hpfx_server', 'http://hpfx.collab.science.gc.ca/')
        try:
            with open(SETTINGS_FILE) as configfile:
                CONFIG.readfp(configfile)
        except:
            logging.info('Creating new config file {}'.format(SETTINGS_FILE))
            with open(SETTINGS_FILE, 'w') as configfile:
                CONFIG.write(configfile)
        BOUNDS = {
            'latitude': {
                'min': int(CONFIG.get('FireGUARD', 'latitude_min')),
                'max': int(CONFIG.get('FireGUARD', 'latitude_max'))
            },
            'longitude': {
                'min': int(CONFIG.get('FireGUARD', 'longitude_min')),
                'max': int(CONFIG.get('FireGUARD', 'longitude_max'))
            }
        }


# HACK: need to do this every time file is loaded or else threads might get to it first
read_config()


def fix_timezone_offset(d):
    """!
    Convert from UTC to local time, respecting DST if required
    @param d Date to fix timezone offset for
    @return Date converted to local time
    """
    local_offset = time.timezone
    if time.daylight:
        if time.localtime().tm_isdst > 0:
            local_offset = time.altzone
    localdelta = datetime.timedelta(seconds=-local_offset)
    # convert to local time so other ftp programs would produce same result
    return (d + localdelta).replace(tzinfo=None)


def save_http(to_dir, url, save_as=None, mode='wb', ignore_existing=False):
    """!
    Save file at given URL into given directory using an HTTP connection
    @param to_dir Directory to save into
    @param url URL to download from
    @param save_as File to save as, or None to use URL file name
    @param mode Mode to write to file with
    @param ignore_existing Whether or not to download if file already exists
    @return Path that file was saved to
    """
    logging.debug("Saving {}".format(url))
    if save_as is None:
        save_as = os.path.join(to_dir, os.path.basename(url))
    print(save_as)
    if ignore_existing and os.path.exists(save_as):
        logging.debug('Ignoring existing file')
        return save_as
    ensure_dir(to_dir)
    # we want to keep modified times matching on both ends
    do_save = True
    req = urllib2.Request(url, headers={'User-Agent': 'WeatherSHIELD/0.93'})
    response = urllib2.urlopen(req)
    modlocal = None
    if 'last-modified' in response.headers.keys():
        mod = response.headers['last-modified']
        modtime = dateutil.parser.parse(mod)
        modlocal = fix_timezone_offset(modtime)
        # if file exists then compare mod times
        if os.path.isfile(save_as):
            filetime = os.path.getmtime(save_as)
            filedatetime = datetime.datetime.fromtimestamp(filetime)
            do_save = modlocal != filedatetime
    # NOTE: need to check file size too? Or should it not matter because we
    #       only change the timestamp after it's fully written
    if do_save:
        logging.info("Downloading {}".format(save_as))
        try:
            filedata = urllib2.urlopen(req)
            with open(save_as, mode) as f:
                while True:
                    tmp = filedata.read(1024 * 1024)
                    if not tmp:
                        break 
                    f.write(tmp)
        except:
            try_remove(save_as)
            raise
        if modlocal is not None:
            tt = modlocal.timetuple()
            usetime = time.mktime(tt)
            os.utime(save_as, (usetime, usetime))
    return save_as


def save_ftp(to_dir, url, user="anonymous", password="", ignore_existing=False):
    """!
    Save file at given URL into given directory using an FTP connection
    @param to_dir Directory to save into
    @param url URL to download from
    @param user User to use for authentication
    @param password Password to use for authentication
    @param ignore_existing Whether or not to download if file already exists
    @return Path that file was saved to
    """
    urlp = urlparse(url)
    folder = os.path.dirname(urlp.path)
    site = urlp.netloc
    filename = os.path.basename(urlp.path)
    logging.debug("Saving {}".format(filename))
    save_as = os.path.join(to_dir, filename)
    print(save_as)
    if os.path.isfile(save_as):
        if ignore_existing:
            logging.debug('Ignoring existing file')
            return save_as
    import ftplib
    #logging.debug([to_dir, url, site, user, password])
    ftp = ftplib.FTP(site)
    ftp.login(user, password)
    ftp.cwd(folder)
    do_save = True
    ftptime = ftp.sendcmd('MDTM {}'.format(filename))
    ftpdatetime = datetime.datetime.strptime(ftptime[4:], '%Y%m%d%H%M%S')
    ftplocal = fix_timezone_offset(ftpdatetime)
    # if file exists then compare mod times
    if os.path.isfile(save_as):
        filetime = os.path.getmtime(save_as)
        filedatetime = datetime.datetime.fromtimestamp(filetime)
        do_save = ftplocal != filedatetime
    # NOTE: need to check file size too? Or should it not matter because we
    #       only change the timestamp after it's fully written
    if do_save:
        logging.debug("Downloading {}".format(filename))
        with open(save_as, 'wb') as f:
            ftp.retrbinary('RETR {}'.format(filename), f.write)
        tt = ftplocal.timetuple()
        usetime = time.mktime(tt)
        os.utime(save_as, (usetime, usetime))
    return save_as


def try_save(fct, url, max_save_retries=5):
    """!
    Use callback fct to try saving up to a fixed number of retries
    @param fct Function to apply to url
    @param url URL to apply function to
    @param max_save_retries Maximum number of times to try saving
    @return Result of calling fct on url
    """
    save_tries = 0
    while (True):
        try:
            return fct(url)
        except urllib.error.URLError as ex:
            logging.warning(ex)
            # no point in retrying if URL doesn't exist
            if 403 == ex.code:
                logging.error(ex.reason)
                raise ex
            if 404 == ex.code or save_tries >= max_save_retries:
                raise ex
            logging.warning("Retrying save for {}".format(url))
            save_tries += 1


def copy_file(filename, toname):
    """!
    Copy file and keep timestamp the same
    @param filename Source path to copy from
    @param toname Destination path to copy to
    @return None
    """
    shutil.copyfile(filename, toname)
    filetime = os.path.getmtime(filename)
    os.utime(toname, (filetime, filetime))


def calc_rh(Td, T):
    """!
    Calculate RH based on dewpoint temp and temp
    @param Td Dewpoint temperature (Celcius)
    @param T Temperature (Celcius)
    @return Relative Humidity (%)
    """
    m = 7.591386
    Tn = 240.7263
    return 100 * pow(10, (m * ((Td / (Td + Tn)) - (T / (T + Tn)))))


def calc_ws(u, v):
    """!
    Calculate wind speed in km/h from U and V wind given in m/s
    @param u Wind vector in U direction (m/s)
    @param v Wind vector in V direction (m/s)
    @return Calculated wind speed (km/h)
    """
    # NOTE: convert m/s to km/h
    return 3.6 * math.sqrt(u * u + v * v)


def calc_wd(u, v):
    """!
    Calculate wind direction from U and V wind given in m/s
    @param u Wind vector in U direction (m/s)
    @param v Wind vector in V direction (m/s)
    @return Wind direction (degrees)
    """
    return ((180 / math.pi * math.atan2(-u, -v)) + 360) % 360


def kelvin_to_celcius(t):
    """!
    Convert temperature in Kelvin to Celcius 
    @param t Temperature (Celcius)
    @return Temperature (Kelvin)
    """
    return t - 273.15

def make_insert_statement(table, columns, no_join=True):
    """!
    Generates INSERT statement for table using column names
    @param table Table to insert into
    @param columns Columns within table
    @param no_join Whether or not to make complex statement with join
    @return INSERT statement that was created
    """
    if no_join:
        return "INSERT INTO {table}({cols}) values ({vals})".format(
                table=table,
                cols=', '.join(columns),
                vals=', '.join([PARAM] * len(columns))
            )
    return """
INSERT INTO {table}({cols})
SELECT {val_cols}
FROM (VALUES ({vals})) val ({cols})
LEFT JOIN {table} d ON
    {join_stmt}
WHERE
    {null_stmt}
    """.format(
        table=table,
        cols=', '.join(columns),
        val_cols=', '.join(map(lambda x: 'val.' + x, columns)),
        join_stmt=' AND '.join(map(lambda x: 'val.' + x + '=d.' + x, columns)),
        null_stmt=' AND '.join(map(lambda x: 'd.' + x + ' IS NULL', columns)),
        vals=', '.join([PARAM] * len(columns))
    )


def make_sub_insert_statement(table, columns, fkId, fkName, fkTable, fkColumns):
    """!
    Generates INSERT statement for table using column names
    @param table Table to insert into
    @param columns Columns within table
    @param fkId Foreign key ID
    @param fkName Foreign key name
    @param fkTable Foreign key table
    @param fkColumns Foreign key table columns
    @return INSERT statement that was created
    """
    # do this instead of using set() so order is kept
    actual_columns = [x for x in columns if x not in fkColumns]
    return """
        INSERT INTO {table}({actual_cols})
        SELECT d.{fkId} AS {fkName}, {val_cols}
        FROM
            (VALUES ({vals})) val ({cols})
            LEFT JOIN {fkTable} d
            ON {join_stmt}
        """.format(
                table=table,
                actual_cols=', '.join([fkName] + actual_columns),
                cols=', '.join(columns),
                vals=', '.join([PARAM] * len(columns)),
                fkId=fkId,
                fkName=fkName,
                val_cols=', '.join(map(lambda x: 'val.' + x, actual_columns)),
                fkTable=fkTable,
                join_stmt=' AND '.join(map(lambda x: 'val.' + x + '=d.' + x, fkColumns))
            )


def fix_None(x):
    """!
    Convert to None instead of alternative formats that mean the same
    @param x Value to convert from
    @return None or the original value
    """
    # for some reason comparing to pd.NaT doesn't work
    return None if isinstance(x, type(pd.NaT)) else None if 'nan' == str(x) else x


def fix_Types(x):
    """!
    Convert to datetime if it's a np.datetime64, or None if it's a value for nothing
    @param x Value to convert from
    @return None, a datetime, or the original value
    """
    # for some reason the dates are giving too much precision for the database to use if seconds are specified
    if isinstance(x, np.datetime64):
        x = pd.to_datetime(x, utc=True)
    if isinstance(x, np.int64):
        x = int(x)
    return fix_None(x)


def fix_execute(cursor, stmt, data):
    """!
    @param cursor Cursor to execute statement with
    @param stmt Statement to execute
    @param data Data to populate statement with
    @return None
    """
    try:
        psycopg2.extras.execute_batch(cursor, stmt, data)
        #cursor.executemany(stmt, (tuple(map(fix_Types, x)) for x in data))
    except psycopg2.Error as e:
        logging.error(e)
        for vals in (tuple(map(fix_Types, x)) for x in data):
            try:
                cursor.execute(stmt, vals)
            except psycopg2.Error as e2:
                logging.error('Error inserting:')
                logging.error(vals)
                logging.error(e2)
                sys.exit(-1)

DB_USER = 'wx_readwrite'
DB_PASSWORD = 'wx_r34dwr1t3p455w0rd!'
#DB_USER = 'docker'
#DB_PASSWORD = 'docker'

def open_local_db():
    """!
    @param dbname Name of database to open, or None to open default
    @return psycopg2 connection to database
    """
    logging.debug("Opening local database connection")
    return psycopg2.connect(dbname='FireGUARD', port=5432, user=DB_USER, password=DB_PASSWORD, host='172.18.0.200')


def save_data(table, wx, delete_all=False, dbname=None):
    """!
    Save into database
    @param table Table to save data into
    @param wx Data to save into table
    @param delete_all Whether or not to delete data from table before saving
    @param dbname Name of database to save to
    @return None
    """
    # open connection
    cnxn = None
    try:
        cnxn = open_local_db(dbname)
        trans_save_data(cnxn, table, wx, delete_all)
        cnxn.commit()
    finally:
        if cnxn:
            cnxn.close()


def trans_delete_data(cnxn, table, wx, delete_all=False):
    """!
    Delete data give from table so that it can be replaced
    @param cnxn Connection to use for query
    @param table Table to insert data into
    @param wx Data to insert into table
    @param delete_all Whether or not to delete all data from table before inserting
    @return None
    """
    cursor = cnxn.cursor()
    # Assumption is that every save we have all points for the included members
    # - still should allow us to save one member at a time though
    if delete_all:
        stmt_delete = "DELETE FROM {}".format(table)
        logging.debug("Deleting existing data using {}".format(stmt_delete))
        cursor.execute(stmt_delete)
    else:
        # DELETE statement that uses all unique values for index columns except coordinates
        non_point_indices = [x for x in wx.index.names if x not in ['latitude', 'longitude']]
        unique = wx.reset_index()[non_point_indices].drop_duplicates()
        stmt_delete = "DELETE FROM {} WHERE {}".format(table,
                                                       ' and '.join(map(lambda x: x + '=' + PARAM, non_point_indices))
                                                       )
        logging.debug("Deleting existing data using {}".format(stmt_delete))
        logging.debug(unique.values)
        if 0 == len(unique.values):
            logging.debug("No data provided - nothing to delete or insert")
            return
        fix_execute(cursor, stmt_delete.format(table), unique.values)


def trans_save_data(cnxn, table, wx, delete_all=False):
    """!
    Save into database with given connection and don't commit
    @param cnxn Connection to use for query
    @param table Table to insert data into
    @param wx Data to insert into table
    @param delete_all Whether or not to delete all data from table before inserting
    @return None
    """
    logging.debug("Saving data to {}".format(table))
    trans_delete_data(cnxn, table, wx, delete_all)
    all_wx = wx.reset_index()
    columns = all_wx.columns
    stmt_insert = make_insert_statement(table, columns)
    trans_insert_data(cnxn, wx, stmt_insert)

def trans_insert_data(cnxn, wx, stmt_insert):
    """!
    Insert data using statement
    @param cnxn Connection to use for query
    @param wx Data to insert into table
    @param stmt_insert INSERT statement to use
    @return None
    """
    cursor = cnxn.cursor()
    index = wx.index.names
    all_wx = wx.reset_index()
    # HACK: this is returning int64 when we know they aren't
    for i in index:
        print("Fixing column " + str(i))
        if 'int64' in str(all_wx[i].dtype):
            all_wx[i] = all_wx[i].astype(int)
    logging.debug("Inserting {} rows into database".format(len(all_wx)))
    # use generator expression instead of list so we don't convert and then use
    fix_execute(cursor, stmt_insert, all_wx.values)


def write_foreign(cnxn, schema, table, index, fct_insert, cur_df):
    """!
    Write data subset for a foreign key table and then merge the generated foreign keys into data
    @param cnxn Connection to use for query
    @param schema Schema that table resides in
    @param table Table to insert into
    @param index List of index keys for table
    @param fct_insert Function to call to insert into table
    @param cur_df DataFrame with data to insert
    @return DataFrame with original data and merged foreign key data
    """
    qualified_table = '{}.{}'.format(schema, table)
    logging.debug('Writing foreign key data to {}'.format(qualified_table))
    new_index = cur_df.index.names
    cur_df = cur_df.reset_index()
    sub_data = cur_df[index].drop_duplicates().set_index(index)
    fct_insert(cnxn, qualified_table, sub_data)
    # should be much quicker to read out the fk data and do a join on this end
    fkData = pd.read_sql("SELECT * FROM {}".format(qualified_table), cnxn)
    print(fkData.columns)
    print(fkData.dtypes)
    for i in range(len(fkData.columns)):
        if fkData.dtypes[i] == 'datetime64[ns]':
            c = fkData.columns[i]
            print('Fixing ' + c)
            fkData[c] = pd.to_datetime(fkData[c], utc=True)
    print(fkData.dtypes)
    fkId = [x for x in fkData.columns if x not in index][0]
    fkColumns = [x for x in fkData.columns if x != fkId]
    new_index = [fkId] + [x for x in new_index if x not in fkColumns]
    columns = [fkId] + [x for x in cur_df.columns if x not in fkColumns]
    cur_df = cur_df.merge(fkData)[columns].set_index(new_index)
    return cur_df

SCHEMA = None
MODELFK = None
FINAL_TABLE = None
DF = None
ADDSTARTDATE = None
def insert_weather(schema, final_table, df, modelFK='generated', addStartDate=True):
    """!
    Insert weather data into table and foreign key tables
    @param schema Schema that table exists in
    @param final_table Table to insert into
    @param df DataFrame with data to insert
    @param modelFK Foreign key to use for inserting into DAT_Model table
    @param addStartDate Whether or not to add start date for weather to data
    @return None
    """
    global SCHEMA
    global MODELFK
    global FINAL_TABLE
    global DF
    global ADDSTARTDATE
    SCHEMA = schema
    MODELFK = modelFK
    FINAL_TABLE = final_table
    DF = df
    ADDSTARTDATE = addStartDate
    # schema = common.SCHEMA
    # modelFK = common.MODELFK
    # final_table = common.FINAL_TABLE
    # addStartDate = ADDSTARTDATE
    # HACK: add column for startdate for run
    def do_insert(cnxn, table, data):
        """Insert and ignore duplicate key failures"""
        stmt_insert = make_insert_statement(table, data.reset_index().columns, False)
        # don't delete and insert without failure
        trans_insert_data(cnxn, data, stmt_insert)
    def do_insert_only(cnxn, table, data):
        """Insert and assume success because no duplicate keys should exist"""
        # rely on deleting from FK table to remove everything from this table, so just insert
        stmt_insert = make_insert_statement(table, data.reset_index().columns)
        trans_insert_data(cnxn, data, stmt_insert)
    if addStartDate:
        df['startdate'] = pd.to_datetime(df.reset_index()['fortime'].min(), utc=True)
    try:
        cnxn = open_local_db()
        cur_df = df
        cur_df = write_foreign(cnxn, schema, 'DAT_Location', ['latitude', 'longitude'], do_insert, cur_df)
        cur_df = write_foreign(cnxn, schema, 'DAT_Model', ['model', modelFK, 'startdate'] if addStartDate else ['model', modelFK], trans_save_data, cur_df)
        cur_df = write_foreign(cnxn, schema, 'DAT_LocationModel', ['modelgeneratedid', 'locationid'], do_insert_only, cur_df)
        logging.debug('Writing data to {}'.format(final_table))
        do_insert_only(cnxn, '{}.{}'.format(schema, final_table), cur_df)
        cnxn.commit()
    finally:
        cnxn.close()

def apply_wind(w):
    return w.apply(calc_wind, axis=1)

def filterXY(data):
    data = data[data[:, :, 0] >= BOUNDS['latitude']['min']]
    data = data[data[:, 0] <= BOUNDS['latitude']['max']]
    data = data[data[:, 1] >= BOUNDS['longitude']['min']]
    data = data[data[:, 1] <= BOUNDS['longitude']['max']]
    return data

def read_all_data(my_wgrib2, coords, mask, matches, indices):
# def read_data(args):
    # coords, mask, select, m = args
    # logging.debug('{} => {}'.format(mask.format(m), select))
    results = wgrib2.get_all_data(my_wgrib2, mask, indices, matches)
    # now we have an array of all the ensemble members
    final = {}
    for m in results.keys():
        final[m] = []
        for r in results[m]:
            data = np.dstack([coords, r])
            data = filterXY(data)
            final[m].append(data[:, 2])
        # logging.debug("Slice")
    return final


k_to_c = np.vectorize(kelvin_to_celcius)


import concurrent.futures

# def read_member(mask, select, coords, member, apcp):
def read_members(my_wgrib2, mask, matches, coords, members, apcp):
    indices = ['TMP', 'RH', 'UGRD', 'VGRD']
    if apcp:
        indices = indices + ['APCP']
    results = read_all_data(my_wgrib2, coords, mask, matches, indices)
    temp = results['TMP']
    rh = results['RH']
    ugrd = results['UGRD']
    vgrd = results['VGRD']
    # temp = read_data(coords, mask, matches, 'TMP')
    # rh = read_data(coords, mask, matches, 'RH')
    # ugrd = read_data(coords, mask, matches, 'UGRD')
    # vgrd = read_data(coords, mask, matches, 'VGRD')
    # logging.debug("Kelvin")
    temp = k_to_c(temp)
    ws = []
    wd = []
    for u, v in zip(ugrd, vgrd):
        # logging.debug("Speed")
        u_2 = u * u
        v_2 = v * v
        sq = u_2 + v_2
        ws.append(3.6 * np.sqrt(sq))
        # logging.debug("Direction")
        a = np.arctan2(-u, -v)
        wd.append(((180 / math.pi * a) + 360) % 360)
    # logging.debug("Stack")
    columns = ['latitude', 'longitude', 'TMP','RH', 'WS', 'WD']
    if apcp:
        # pcp = read_data(coords, mask, matches, 'APCP')
        pcp = results['APCP']
    coords = filterXY(coords)
    # logging.debug("DataFrame")
    results = []
    for i in range(len(members)):
        member = members[i]
        wx = pd.DataFrame(coords, columns=['latitude', 'longitude'])
        wx['TMP'] = temp[i]
        wx['RH'] = rh[i]
        wx['WS'] = ws[i]
        wx['WD'] = wd[i]
        wx['APCP'] = pcp[i] if apcp else 0
        wx['Member'] = member
        results.append(wx)
    # logging.debug("Done")
    return pd.concat(results)

from multiprocessing import Pool

def read_grib(mask, apcp=True):
    """!
    Read grib data for desired time and field
    @param mask File mask for path to source grib2 file to read
    @return DataFrame with data read from file    
    """
    my_wgrib2 = wgrib2.open()
    matches = wgrib2.match(my_wgrib2, mask.format('TMP'))
    members = list(map(lambda x: 0 if -1 != x.find('low-res ctl') else int(x[x.find('ENS=') + 4:]), matches))
    matches = list(map(lambda x: x[x.rfind(':'):], matches))
    coords = wgrib2.coords(my_wgrib2, mask.format('TMP'))
    results = read_members(my_wgrib2, mask, matches, coords, members, apcp)
    # logging.debug(output)
    output = results.set_index(['latitude', 'longitude', 'Member'])
    output = output[['TMP', 'RH', 'WS', 'WD', 'APCP']]
    wgrib2.close(my_wgrib2)
    del my_wgrib2
    # need to add fortime and generated
    return output

def try_remove(file):
    """!
    Delete file but ignore errors if can't while raising old error
    @param file Path to file to delete
    @return None
    """
    try:
        logging.debug("Trying to delete file {}".format(file))
        os.remove(file)
    except:
        pass


def download(get_what, suppress_exceptions=True):
    """!
    Download URL using specified proxy
    @param get_what Array of proxy and URL to use
    @param suppress_exceptions Whether or not return exception instead of raising it
    @return Contents of URL, or exception
    """
    try:
        url = get_what
        # HACK: check this to make sure url completion has worked properly
        assert('{}' not in url)
        response = urllib2.urlopen(url)
        # logging.debug("Saving {}".format(url))
        return response.read()
    except urllib.error.URLError as ex:
        # provide option so that we can call this from multiprocessing and still handle errors
        if suppress_exceptions:
            # HACK: return type and url for exception
            return {'type': type(ex), 'url': url}
        ex.url = url
        raise ex


def download_many(urls, fct=download):
    """!
    Download multiple URLs using current proxy settings
    @param urls List of multiple URLs to download
    @param processes Number of processes to use for downloading
    @return List of paths that files have been saved to
    """
    get_what = list(urls)
    # HACK: use current proxy so we don't do check for proxy and delay this
    results = list(map(fct, get_what))
    for i, result in enumerate(results):
        if isinstance(result, dict):
            # HACK: recreate error by trying to open it again
            # if this works this time then everything is fine right?
            results[i] = fct(get_what[i], suppress_exceptions=False)
    return results


def split_line(line):
    """!
    Split given line on whitespace sections
    @param line Line to split on whitespace
    @return Array of strings after splitting
    """
    return re.sub(r' +', ' ', line.strip()).split(' ')

