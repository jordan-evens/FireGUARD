#############  setup commands
mkdir -p data/generated/tiled
docker-compose stop
docker-compose rm -f
docker-compose build
docker-compose up -d
docker-compose exec -e PGPASSWORD=docker db psql FireGUARD -U docker -p 5432 -h localhost -f /FireGUARD/postgre.sql
docker-compose run --rm wxcli python reanalysis1.py

#############  utility commands that are useful

#############  wxcli python container
# docker compose run --rm wxcli /bin/bash
# docker compose run --rm wxcli python update.py

#############  gis python container
# docker compose run --rm gis /bin/bash

#############  database access
# docker exec -it fireguard-db psql -U docker -h localhost -d FireGUARD -p 5432

# select pg_size_pretty(pg_database_size('FireGUARD'));


#############  wxshield web page
# docker compose exec wxshield /bin/bash

#############  firestarr cli
# docker compose run --rm firestarr /bin/bash

#############  test firestarr
# docker compose run --rm firestarr ./FireSTARR ./Data/output 2017-08-27 52.01 -89.024 12:15 -v --wx Data/output/wx.csv --ffmc 90 --dmc 40 --dc 300 --apcp_0800 0
