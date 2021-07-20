#############  setup commands
mkdir -p data/generated/tiled
mkdir -p data/wx/longrange
docker-compose stop
docker-compose rm -f
docker-compose build
docker-compose up -d
docker-compose exec -e PGPASSWORD=docker db psql FireGUARD -U docker -p 5432 -h localhost -f /FireGUARD/postgre.sql
cp setup/lib/longrange_200001010000.csv data/wx/longrange/
docker-compose run --rm wxcli python load_previous.py historic
# needs to run once to have historic data
# docker-compose run --rm wxcli python reanalysis1.py
# need to run this frequently enough to get data as it gets released
# docker-compose run --rm wxcli python update.py

#############  utility commands that are useful

#############  wxcli python container
# docker-compose exec wxcli /bin/bash
# docker-compose exec wxcli python update.py

#############  gis python container
# docker-compose run --rm gis /bin/bash

#############  database access
# docker-compose exec -e PGPASSWORD=docker db psql --username=docker --host=db -d FireGUARD -p 5432

# select pg_size_pretty(pg_database_size('FireGUARD'));


#############  wxshield web page
# docker-compose exec wxshield /bin/bash

#############  firestarr cli
# docker-compose run --rm firestarr /bin/bash

#############  test firestarr
# docker-compose run --rm firestarr ./FireSTARR ./Data/output 2017-08-27 52.01 -89.024 12:15 -v --wx Data/output/wx.csv --ffmc 90 --dmc 40 --dc 300 --apcp_0800 0
