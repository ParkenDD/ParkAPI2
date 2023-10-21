FROM python:3.11
LABEL maintainer="Holger Bruch <hb@mfdz.de>"


RUN apt-get install 
RUN apt-get update && apt-get install -y \
  libpq-dev libgdal-dev libproj-dev libgeos-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
COPY web/scrapers/ParkAPI2_sources/requirements.txt /app/web/scrapers/ParkAPI2_sources/

RUN pip install -r requirements.txt -r web/scrapers/ParkAPI2_sources/requirements.txt

COPY . /app

EXPOSE 8000
ENTRYPOINT ["sh", "/app/entrypoint.sh"]
CMD runserver 0.0.0.0:8000
