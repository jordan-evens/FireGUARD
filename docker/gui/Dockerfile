FROM php:7.2-apache
RUN apt-get update
RUN apt-get install -y libpq-dev \
  && docker-php-ext-configure pgsql -with-pgsql=/usr/local/pgsql \
  && docker-php-ext-install pdo pdo_pgsql pgsql
RUN apt-get install -y wget unzip
WORKDIR /var/www/html/wxshield/
RUN wget https://github.com/twbs/bootstrap/releases/download/v3.4.1/bootstrap-3.4.1-dist.zip
RUN unzip bootstrap-3.4.1-dist.zip
RUN mv bootstrap-3.4.1-dist bootstrap
RUN rm bootstrap-3.4.1-dist.zip
WORKDIR /var/www/html/wxshield/js/
RUN wget https://code.jquery.com/jquery-1.11.3.js
RUN wget https://code.jquery.com/jquery-1.11.3.min.js
RUN wget https://github.com/jquery-validation/jquery-validation/archive/1.11.1.zip
RUN unzip 1.11.1.zip
RUN mv jquery-validation-1.11.1/jquery.validate.js ./
RUN wget https://github.com/MrRio/jsPDF/archive/v1.2.61.zip
RUN unzip v1.2.61.zip
RUN mkdir -p jspdf & mv jsPDF-1.2.61/dist/jspdf.min.js jspdf/jspdf.js
# FIX: this shouldn't be static
COPY settings.ini /var/www/html/wxshield
COPY WeatherSHIELD/gui/ /var/www/html/wxshield/
