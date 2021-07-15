"""Load GEPS data"""

from gribloader import GribLoader

from weatherloader import WeatherLoader
import datetime
import urllib.request as urllib2

import glob
import sys
sys.path.append('../util')
import common
import os
import pandas as pd
import logging
import socket
import time
from multiprocessing import Pool

# don't set too high so we're nice about downloading things
DOWNLOAD_THREADS = 6

def read_wx(args):
    dir, name, for_run, for_date = args
    # logging.debug("for_date=" + str(for_date))
    # logging.debug("for_run=" + str(for_run))
    diff = for_date - for_run
    real_hour = int((diff.days * 24) + (diff.seconds / 60 / 60))
    logging.debug("{} {} + {:03d}h".format(name, for_run, real_hour))
    date = for_run.strftime(r'%Y%m%d')
    time = int(for_run.strftime(r'%H'))
    save_as = '{}_{}{:02d}_{}_{:03d}'.format(name, date, time, "{}", real_hour)
    result = common.read_grib(os.path.join(dir, save_as), 0 != real_hour)
    # need to add fortime and generated
    result['generated'] = pd.to_datetime(for_run, utc=True)
    result['fortime'] = pd.to_datetime(for_date, utc=True)
    index = result.index.names
    columns = result.columns
    result = result.reset_index()
    result['model'] = name
    # logging.debug(result)
    return result.set_index(index + ['model'])[columns]

def do_save(args):
    """!
    Generate URL containing data
    @param weather_index WeatherIndex to get files for
    """
    host, dir, mask, save_dir, date, time, real_hour, save_as, weather_index = args
    # Get full url for the file that has the data we're asking for
    partial_url = r'{}{}{}'.format(host,
                                   dir.format(date, time, real_hour),
                                   mask.format('{}', '{}', date, time, real_hour))
    partial_url = partial_url.format(weather_index.name, weather_index.layer)
    def save_file(partial_url):
        """!
        Save the given url
        @param partial_url Partial url to use for determining name
        @return Path saved to when using URL to retrieve
        """
        out_file = os.path.join(save_dir, save_as.format(weather_index.name))
        if os.path.isfile(out_file):
            # HACK: no timestamp so don't download if exists
            # logging.debug("Have {}".format(out_file))
            return out_file
        # logging.debug("Downloading {}".format(out_file))
        try:
            common.save_http(save_dir, partial_url, save_as=out_file)
        except:
            # get rid of file that's there if there was an error
            common.try_remove(out_file)
            raise
        return out_file
    return common.try_save(save_file, partial_url)

class HPFXLoader(WeatherLoader):
    """Loads NAEFS data from NOMADS"""
    # Provide mapping between fields we're looking for and the file names that contain them
    class WeatherIndex(object):
        """Simple class for mapping indices to lookup data"""
        def __init__(self, name, match, layer):
            """!
            An index in the grib data that gets processed
            @param self Pointer to this
            @param name Name of the index
            @param match Array of what to match
            @param layer Layer in the grib data to read for index
            """
            ## Name of the index
            self.name = name
            ## Field in the grib data to read for index
            self.match = match
            ## Layer in the grib data to read for index
            self.layer = layer
    ## The indices that get processed when loading weather
    indices = {
        'TMP': WeatherIndex('TMP', [':TMP', ':2 m above ground:'], 'TGL_2m'),
        'UGRD': WeatherIndex('UGRD', [':UGRD', ':10 m above ground:'], 'TGL_10m'),
        'VGRD': WeatherIndex('VGRD', [':VGRD', ':10 m above ground:'], 'TGL_10m'),
        'RH': WeatherIndex('RH', [':RH', ':2 m above ground:'], 'TGL_2m'),
        'APCP': WeatherIndex('APCP', [':APCP', ':surface:'], 'SFC_0')
    }
    def get_nearest_run(self, interval):
        """!
        Find time of most recent run with given update interval
        @param self Pointer to self
        @param interval How often model is run (hours)
        @return datetime for closest model run to current time
        """
        now = datetime.datetime.now()
        nearest_run = int(interval * round(now.hour / interval)) % 24
        return datetime.datetime.combine(now.date(), datetime.time(nearest_run))
    def load_past_records(self, year=None, force=False):
        """!
        Determine which past run files we have and load them
        @param self Pointer to self
        @param year Year to load files for, or None to load all years
        @param force Whether or not to force loading if records already exist
        @return None
        """
        import glob
        files = glob.glob(self.DIR_DATA)
        runs = list(set([os.path.basename(d) for d in files]))
        # sort so we do the dates chronologically
        runs.sort()
        for run in runs:
            for_run = datetime.datetime.strptime(run, '%Y%m%d%H')
            try:
                if not year or for_run.year == year:
                    self.load_specific_records(for_run, force)
            except:
                logging.error("Unable to load run for {}".format(for_run))
    def load_specific_records(self, for_run, force=False):
        """!
        Load records for specific period
        @param self Pointer to self
        @param for_run Which run of model to use
        @param force Whether or not to force loading if records already exist
        @return Timestamp of run that records were loaded for
        """
        # save into database that corresponds to the start of this run
        # if at any point for_run is already in the database then we're done
        # want to put the data into the database for the start date but check if it exists based on for_run
        if not force:
            logging.debug('Checking if data is already present for {} model generated at {}'.format(self.name, for_run))
            exists = self.check_exists(for_run)
            if exists:
                logging.debug('Data already loaded - aborting')
                return pd.Timestamp(for_run)
        results = []
        start_hours = 8 * 24
        first_step = 3
        first_hours = (list(map(lambda x : x * first_step, range(int(start_hours / first_step)))) + [start_hours])
        last_step = 6
        total_hours = max(self.for_days) * 24
        last_hours = (list(map(lambda x : x * last_step, range(int(total_hours / last_step)))) + [total_hours])
        # logging.debug(first_hours)
        # logging.debug(last_hours)
        hours = list(dict.fromkeys(first_hours + last_hours))
        date = for_run.strftime(r'%Y%m%d')
        time = int(for_run.strftime(r'%H'))
        save_dir = common.ensure_dir(os.path.join(self.DIR_DATA, '{}{:02d}'.format(date, time)))
        args = []
        for hour in hours:
            logging.info("Downloading {} records from {} run for hour {}".format(self.name, for_run, hour))
            for_date = for_run + datetime.timedelta(hours=hour)
            diff = for_date - for_run
            real_hour = int((diff.days * 24) + (diff.seconds / 60 / 60))
            save_as = '{}_{}{:02d}_{}_{:03d}'.format(self.name, date, time, "{}", real_hour)
            for_what = ['TMP', 'UGRD', 'VGRD', 'RH']
            if 0 != real_hour:
                for_what = for_what + ['APCP']
            for_what = list(map(lambda x: self.indices[x], for_what))
            n = len(for_what)
            args = args + list(zip([self.host] * n, [self.dir] * n, [self.mask] * n, [save_dir] * n, [date] * n, [time] * n, [real_hour] * n, [save_as] * n, for_what))
        pool = Pool(DOWNLOAD_THREADS)
        pool.map(do_save, args)
        actual_dates = list(map(lambda hour: for_run + datetime.timedelta(hours=hour), hours))
        n = len(actual_dates)
        # more than the number of cpus doesn't seem to help
        pool = Pool(os.cpu_count())
        results = list(pool.map(read_wx,
                               zip([save_dir] * n,
                                   [self.name] * n,
                                   [for_run] * n,
                                   actual_dates)))
        # don't save data until everything is loaded
        wx = pd.concat(results)
        self.save_data(wx)
        logging.debug("Done")
        # return the run that we ended up loading data for
        # HACK: Timestamp format is nicer than datetime's
        return pd.Timestamp(for_run)
    def load_records(self, max_retries=15, force=False):
        """!
        Load the latest records using the specified interval to determine run
        @param self Pointer to self
        @param max_retries Maximum number of retries before failure
        @param force Whether or not ot force loading if records already exist
        @return None
        """
        for_run = self.get_nearest_run(self.interval)
        for i in range(max_retries):
            try:
                return self.load_specific_records(for_run)
            except urllib2.HTTPError as ex:
                logging.error(ex)
                # HACK: we set the URL in the place the error originated from
                logging.error(ex.url)
                if i + 1 == max_retries:
                    logging.critical("Too many failures - unable to retrieve data")
                    raise
                for_run = for_run + datetime.timedelta(hours=-self.interval)
                logging.error("**** Moving back 1 run since data is unavailable. Now looking for {}".format(for_run.strftime("%Y%m%d%H")))
    def __init__(self, name, for_days, interval, mask, dir, num_members, no_download=False):
        """!
        Instantiate class
        @param name Name for weather being loaded
        @param for_days Which days to load for
        @param interval how often this data gets updated (hours)
        @param interval distance between time steps (hours)
        @param mask Mask to use for making URL to download
        @param dir Subdirectory to download files from
        #param num_members Number of ensemble members (including control)
        @param no_download Whether or not to not download files
        """
        super(HPFXLoader, self).__init__(name, for_days, no_download)
        ## how often this data gets updated (hours)
        self.interval = interval
        ## URL root to download from
        self.host = common.CONFIG.get('FireGUARD', 'hpfx_server')
        ## Mask to use for making URL to download
        self.mask = mask
        ## Subdirectory to download files from
        self.dir = dir
        ## Number of ensemble members (including control)
        self.num_members = num_members


class GepsLoader(HPFXLoader):
    """ Loads GEPS data """
    def __init__(self, no_download=False):
        """!
        Instantiate class
        @param no_download Whether or not to not download if data already exists
        """
        name = 'GEPS'
        ## Mask to use for making URL to download
        mask = r'CMC_geps-raw_{}_{}_latlon0p5x0p5_{}{:02d}_P{:03d}_allmbrs.grib2'
        ## Subdirectory to download files from
        dir = r'{}/WXO-DD/ensemble/geps/grib2/raw/{:02d}/{:03d}/'
        super(GepsLoader, self).__init__(name=name,
                                         for_days=range(1, 17),
                                         interval=12,
                                         mask=mask,
                                         dir=dir,
                                         num_members=21,
                                         no_download=no_download)


if __name__ == "__main__":
    GepsLoader().load_records()
