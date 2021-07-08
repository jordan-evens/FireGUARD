# syntax=docker/dockerfile:1
FROM python:3.6-slim
WORKDIR /FireGUARD
COPY docker/python/requirements.txt requirements.txt
RUN pip install -r requirements.txt
WORKDIR /FireGUARD/WeatherSHIELD/
RUN apt-get update \
	&& apt-get install -y gcc make gfortran wget
RUN wget ftp://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/wgrib2.tgz.v3.0.2\
	&& tar -xzvf wgrib2.tgz.v3.0.2
WORKDIR /FireGUARD/WeatherSHIELD/grib2
RUN export CC=gcc \
	&& export FC=gfortran \
	&& export COMP_SYS=gnu_linux \
	&& make
RUN mv wgrib2/wgrib2 ../wgrib2
RUN export CC=gcc \
	&& export FC=gfortran \
	&& export COMP_SYS=gnu_linux \
	&& make clean
RUN apt-get purge -y --auto-remove gcc make gfortran
RUN apt-get install -y libgfortran5 libgomp1
WORKDIR /FireGUARD/WeatherSHIELD
RUN rm -rf grib2
WORKDIR /FireGUARD
RUN mkdir data
COPY WeatherSHIELD /FireGUARD/WeatherSHIELD/
COPY util /FireGUARD/util/
