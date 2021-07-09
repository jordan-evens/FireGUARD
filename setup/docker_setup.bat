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

@REM gis python container
docker compose run --rm gis /bin/bash

@REM database access
docker exec -it fireguard-db psql -U docker -h localhost -d FireGUARD -p 5432

@REM wxshield web page
docker compose exec wxshield /bin/bash


:end
