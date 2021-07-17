docker-compose build
docker-compose up -d
docker-compose exec -e PGPASSWORD=docker db psql FireGUARD -U docker -p 5432 -h localhost -f /FireGUARD/postgre.sql
docker-compose run --rm wxcli python reanalysis1.py
