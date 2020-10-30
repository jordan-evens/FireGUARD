import os
import ConfigParser

class Settings:
    def __init__(self):
        from_file = 'settings.ini'
        config = ConfigParser.RawConfigParser()
        if os.path.exists(from_file):
            config.read(from_file)
        else:
            config.add_section('GIS')
            config.set('GIS', 'latitude_min', 41.0)
            config.set('GIS', 'latitude_max', 57.0)
            config.set('GIS', 'longitude_min', -96.0)
            config.set('GIS', 'longitude_max', -73.0)
        with open(from_file, 'wb') as to_file:
            config.write(to_file)
        self.latitude_min = float(config.get('GIS', 'latitude_min'))
        self.latitude_max = float(config.get('GIS', 'latitude_max'))
        self.longitude_min = float(config.get('GIS', 'longitude_min'))
        self.longitude_max = float(config.get('GIS', 'longitude_max'))

