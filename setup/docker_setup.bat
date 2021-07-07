docker volume create fireguard_data
docker network create fireguard-network
docker run --name fireguard-postgis  -v fireguard_data:/var/lib/postgresql --network fireguard-network -e POSTGRES_PASSWORD="p455w0rd!" -d postgis/postgis
docker run --name fireguard-cli -it --rm -v fireguard_data:/var/lib/postgresql --network fireguard-network thinkwhere/gdal-python python


@rem docker run -it --rm --network fireguard-network postgis/postgis psql -h fireguard-postgis -U postgres


@rem docker run --name fireguard-cli -v fireguard_data:/var/lib/postgresql --network fireguard-network thinkwhere/gdal-python

REM docker run --name fireguard-cli -it --rm -v postgis-data:/var/lib/postgresql --network fireguard-network thinkwhere/gdal-python python

docker exec -it fireguard_db_1 psql -U docker -h localhost -d gis -p 5432
docker exec -it fireguard-db psql -U docker -h localhost -d gis -p 5432

docker run -it --network fireguard-network fireguard-python /bin/bash

# bash
cd ~
python3 -m venv fireguard
source fireguard/bin/activate
python -m pip install --upgrade pip
pip install cython
pip install psycopg2
pip install postgis


# python
import psycopg2
conn = psycopg2.connect(dbname='FireGUARD', port=5432, user='docker', password='docker', host='172.18.0.2')
cursor = conn.cursor()
cursor.execute('SELECT * FROM INPUTS.DISTANCE(46, -85, 47, -90);')
for i, record in enumerate(cursor):
	print("\n", type(record))
	print(record)

cursor.close()
conn.close()

# build python docker
docker build --tag fireguard-python .

# build from main directory
docker build --tag fireguard-python -f docker/python/Dockerfile . && docker run -it --rm --name fireguard-cli -v C:\FireGUARD\data:/FireGUARD/data --network fireguard-network fireguard-python /bin/bash

docker exec -it --rm --name fireguard-cli -v C:\FireGUARD\data:/FireGUARD/data --network fireguard-network fireguard-python /bin/bash