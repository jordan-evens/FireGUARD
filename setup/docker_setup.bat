@REM setup commands
docker network create --subnet 172.18.0.0/16 fireguard-network
docker compose build
docker compose up -d
docker compose exec -e PGPASSWORD=docker db psql FireGUARD -U docker -p 5432 -h localhost -f /FireGUARD/postgre.sql
docker compose run --rm wxcli python reanalysis1.py

goto :end

@REM utility commands that are useful

@REM wxcli python container
docker compose run --rm wxcli /bin/bash
docker compose run --rm wxcli python update.py

@REM gis python container
docker compose run --rm gis /bin/bash

@REM database access
docker exec -it fireguard-db psql -U docker -h localhost -d FireGUARD -p 5432

@REM wxshield web page
docker compose exec wxshield /bin/bash

@REM firestarr cli
docker compose run --rm firestarr /bin/bash
@REM test firestarr
docker compose run --rm firestarr ./FireSTARR ./Data/output 2017-08-27 52.01 -89.024 12:15 -v --wx Data/output/wx.csv --ffmc 90 --dmc 40 --dc 300 --apcp_0800 0


:end
