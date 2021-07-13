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
    def read_grib(self, for_run, for_date, name, download_only=False):
        """!
        Read grib data for desired time and field
        @param self Pointer to this
        @param for_run Which run of model to use
        @param for_date Which date of model to use
        @param name Name of index to read
        @return Index data as a pd dataframe
        """
        def get_match_files(weather_index):
            """!
            Generate URL containing data
            @param weather_index WeatherIndex to get files for
            """
            # Get full url for the file that has the data we're asking for
            diff = for_date - for_run
            real_hour = int((diff.days * 24) + (diff.seconds / 60 / 60))
            print("real_hour=" + str(real_hour))
            date = for_run.strftime(r'%Y%m%d')
            time = int(for_run.strftime(r'%H'))
            #mask = r'CMC_geps-raw_{}_{}_latlon0p5x0p5_{}{:02d}_P{:03d}_allmbrs.grib2'
            file = self.mask.format(weather_index.name, weather_index.layer, date, time, for_run.hour)
            #dir = r'{}/WXO-DD/ensemble/geps/grib2/raw/{:02d}/{:03d}/'
            dir = self.dir.format(date, time, for_run.hour)
            partial_url = r'{}{}{}'.format(self.host, dir, file)
            def get_local_name():
                """!
                Return file name that will be saved locally
                @return Path to save to locally when using URL to retrieve
                """
                save_as = '{}_{}{:02d}_{}_{:03d}'.format(self.name, date, time, weather_index.name, real_hour)
                return os.path.join(self.DIR_DATA, save_as)
            def save_file(partial_url):
                """!
                Save the given url
                @param partial_url Partial url to use for determining name
                @return Path saved to when using URL to retrieve
                """
                out_file = get_local_name()
                if os.path.isfile(out_file):
                    # HACK: no timestamp so don't download if exists
                    return out_file
                logging.debug("Downloading {}".format(out_file))
                urls = [partial_url]
                results = common.download_many(urls, fct=common.download)
                try:
                    # logging.debug("Writing file")
                    with open(out_file, "wb") as f:
                        for result in results:
                            f.write(result)
                except:
                    # get rid of file that's there if there was an error
                    common.try_remove(out_file)
                    raise
                return out_file
            if self.no_download:
                # return file that would have been saved without actually trying to save it
                return get_local_name(partial_url)
            return common.try_save(save_file, partial_url)
        weather_index = self.indices[name]
        file = get_match_files(weather_index)
        if download_only:
            return None
        # result = common.read_grib(file, weather_index.name)
        # index = result.index.names
        # columns = result.columns
        # result = result.reset_index()
        # result['model'] = self.name
        # return result.set_index(index + ['model'])[columns]
    def read_wx(self, for_run, for_date, download_only=False):
        """!
        Read all weather for given day
        @param self Pointer to self
        @param for_run Which run of model to use
        @param for_date Which date of model to use
        @return Weather as a pd dataframe
        """
        print("for_date=" + str(for_date))
        print("for_run=" + str(for_run))
        def read_temp():
            return self.read_grib(for_run, for_date, 'TMP', download_only)
        def read_ugrd():
            return self.read_grib(for_run, for_date, 'UGRD', download_only)
        def read_vgrd():
            return self.read_grib(for_run, for_date, 'VGRD', download_only)
        def read_rh():
            return self.read_grib(for_run, for_date, 'RH', download_only)
        def read_precip():
            if 0 == for_date.hour:
                return None
            return self.read_grib(for_run, for_date, 'APCP', download_only)
        temp = read_temp()
        rh = read_rh()
        ugrd = read_ugrd()
        vgrd = read_vgrd()
        rain = read_precip()
        if download_only:
            return None
        diff = for_date - for_run
        real_hour = int((diff.days * 24) + (diff.seconds / 60 / 60))
        date = for_run.strftime(r'%Y%m%d')
        time = int(for_run.strftime(r'%H'))
        save_as = '{}_{}{:02d}_{}_{:03d}'.format(self.name, date, time, "{}", real_hour)
        result = common.read_grib(os.path.join(self.DIR_DATA, save_as), 0 != for_date.hour)
        # need to add fortime and generated
        result['generated'] = pd.to_datetime(for_run, utc=True)
        result['fortime'] = pd.to_datetime(for_date, utc=True)
        index = result.index.names
        columns = result.columns
        result = result.reset_index()
        result['model'] = self.name
        print(result)
        return result.set_index(index + ['model'])[columns]
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
        files = glob.glob(self.DIR_DATA + '/{}_*_TMP*'.format(self.name))
        def file_run(file):
            start = file.index('_') + 1
            end = file.index('_', start)
            return file[start:end]
        runs = list(set([file_run(d) for d in files]))
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
        # HACK: +1 so last hour is included
        total_hours = max(self.for_days) * 24
        for hour in (list(map(lambda x : x * self.step, range(int(total_hours / self.step)))) + [total_hours]):
            logging.info("Downloading {} records from {} run for hour {}".format(self.name, for_run, hour))
            actual_date = for_run + datetime.timedelta(hours=hour)
            self.read_wx(for_run, actual_date, download_only=True)
        for hour in (list(map(lambda x : x * self.step, range(int(total_hours / self.step)))) + [total_hours]):
            logging.info("Loading {} records from {} run for hour {}".format(self.name, for_run, hour))
            actual_date = for_run + datetime.timedelta(hours=hour)
            results.append(self.read_wx(for_run, actual_date))
        # don't save data until everything is loaded
        wx = pd.concat(results)
        self.save_data(wx)
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
    def __init__(self, name, for_days, interval, step, mask, dir, num_members, no_download=False):
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
        ## distance between time steps (hours)
        self.step = step
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
                                         for_days=range(1, 16),
                                         interval=6,
                                         step=3,
                                         mask=mask,
                                         dir=dir,
                                         num_members=21,
                                         no_download=no_download)


if __name__ == "__main__":
    GepsLoader().load_records()
