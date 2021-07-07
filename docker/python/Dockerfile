# syntax=docker/dockerfile:1
FROM python:3.6-slim
WORKDIR /FireGUARD
COPY docker/python/requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY WeatherSHIELD /FireGUARD/WeatherSHIELD/
COPY util /FireGUARD/util/
RUN mkdir /FireGUARD/data
WORKDIR /FireGUARD/WeatherSHIELD/
