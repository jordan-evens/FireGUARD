"""Load previous records that aren't in database"""

import sys

if __name__ == "__main__":
    ## year to load for
    year = None
    if len(sys.argv) > 1 and sys.argv[1] not in ['historic', 'geps', 'gefs']:
        year = int(sys.argv[1])
        print("Loading year {}".format(year))
    if len(sys.argv) == 1 or 'historic' in sys.argv:
        import gethistoric
        gethistoric.load_past_records(year)
    if len(sys.argv) == 1 or 'geps' in sys.argv:
        import gepsloader
        loader = gepsloader.GepsLoader(True)
        loader.load_past_records(year)
    if len(sys.argv) == 1 or 'gefs' in sys.argv:
        import gefsloader
        loader = gefsloader.GefsLoader(True)
        loader.load_past_records(year)
