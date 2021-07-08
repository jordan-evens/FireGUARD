# syntax=docker/dockerfile:1
FROM python:3.6-slim
WORKDIR /FireGUARD
COPY docker/python/requirements.txt requirements.txt
WORKDIR /FireGUARD/WeatherSHIELD/
RUN pip install -r /FireGUARD/requirements.txt \
	&& apt-get update \
	&& apt-get install -y gcc make gfortran wget \
	&& wget ftp://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/wgrib2.tgz.v3.0.2 \
	&& tar -xzvf wgrib2.tgz.v3.0.2 \
	&& rm wgrib2.tgz.v3.0.2 \
	&& cd /FireGUARD/WeatherSHIELD/grib2 \
	&& export CC=gcc \
	&& export FC=gfortran \
	&& export COMP_SYS=gnu_linux \
	&& make \
	&& mv wgrib2/wgrib2 ../wgrib2 \
	&& make clean \
	&& apt-get purge -y --auto-remove gcc make gfortran \
	&& apt-get install -y libgfortran5 libgomp1 \
	&& apt-get clean && rm -rf /var/lib/apt/lists/* \
	&& rm -rf \
      /usr/share/man/* \
      /usr/includes/* \
      /var/cache/apk/* \
      /root/.npm/* \
      /usr/lib/node_modules/npm/man/* \
      /usr/lib/node_modules/npm/doc/* \
      /usr/lib/node_modules/npm/html/* \
      /usr/lib/node_modules/npm/scripts/* \
	  /FireGUARD/WeatherSHIELD/grib2 \
	&& mkdir /FireGUARD/data
COPY WeatherSHIELD /FireGUARD/WeatherSHIELD/
COPY util /FireGUARD/util/
