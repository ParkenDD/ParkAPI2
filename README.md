# offenesdresden/ParkAPI rewrite in Django

This is an attempt to rewrite the [ParkAPI](https://github.com/offenesdresden/ParkAPI/)
using [GeoDjango](https://docs.djangoproject.com/en/3.2/ref/contrib/gis/) and
the [django rest framework](https://www.django-rest-framework.org/).


## Data 

Parking lots are identified by a unique string ID. Each one is tied to a *Pool* which 
represents the source of the parking lot data (a website).

Example, query all nearby parking lots (100km around lon:6 lat:50):
```shell script
$ curl "http://localhost:8000/api/v2/lots/?location=6,50&radius=100"
{
  "count": 13,
  "next": null,
  "previous": null,
  "results": [
    {
      "pool_id": "apag",
      "coordinates": [
        6.076306,
        50.767823
      ],
      "latest_data": {
        "timestamp": "2021-11-26T10:08:30",
        "lot_timestamp": null,
        "status": "open",
        "num_free": 6,
        "capacity": 70,
        "num_occupied": 64,
        "percent_free": 8.57
      },
      "date_created": "2021-11-25T11:44:03.917080",
      "date_updated": "2021-11-25T16:26:37.914537",
      "lot_id": "aachen-parkplatz-luisenhospital",
      "name": "Luisenhospital",
      "address": "Parkplatz Luisenhospital\nBoxgraben 99\n52064\nAachen",
      "type": "lot",
      "max_capacity": 70,
      "has_live_capacity": false,
      "public_url": "https://www.apag.de/parkobjekte/parkplatz-luisenhospital",
      "source_url": "https://www.apag.de/parken-in-aachen"
    },
    ...
  ]
}
```

Find the corresponding pool:

```shell script
curl "http://localhost:8000/api/v2/pools/apag/" -H "Accept: application/json; indent=2"
{
  "date_created": "2021-11-25T11:44:03.868010",
  "date_updated": "2021-11-25T11:44:03.868027",
  "pool_id": "apag",
  "name": "Aachener Parkhaus GmbH",
  "public_url": "https://www.apag.de",
  "source_url": null,
  "license": null
}
```

### Original API

```shell script
curl "http://localhost:8000/api/Jena" -H "Accept: application/json; indent=2"
{
  "last_downloaded": "2021-11-29T12:36:00",
  "last_updated": null,
  "lots": [
    {
      "address": null,
      "coords": {
        "lat": 50.927818,
        "lng": 11.585724
      },
      "forecast": false,
      "free": 36,
      "id": "jena-city-carree",
      "lot_type": "Parkplatz",
      "name": "City Carree",
      "region": null,
      "state": "open",
      "total": 40
    },
    ...
  ]
}
```


## Scraping

A prototype is developed in [web/scrapers/builtin/](web/scrapers/builtin/).


## Setup for development

### Clone repo and setup python environment

```shell script
git clone https://github.com/defgsus/ParkAPI2
cd ParkAPI2

virtualenv -p python3 env
source env/bin/activate

pip install -r requirements.txt
pip install -r web/scrapers/builtin/requirements.txt
```

### Create a postgres database

Please follow the instructions in the 
[postgis requirements](https://postgis.net/docs/postgis_installation.html#install_requirements)
to install all necessary packages. 

On debian, setup looks like:
```sh
# see https://www.postgresql.org/download/linux/debian/
apt-get install postgresql-13

# postgis extension utilities 
apt-get install libpq-dev libgdal-dev libproj-dev libgeos-dev postgresql-13-postgis-3-scripts
```
 
Alternatively, you can run the 
[postgis docker image](https://github.com/postgis/docker-postgis):
```shell script
docker run --name some-postgis -e POSTGRES_PASSWORD=<the password> -d postgis/postgis
```

#### Setup and create database
 
First copy the [web/.env.example](web/.env.example) file to `web/.env` and edit.
Specifically `POSTGRES_USER` and `POSTGRES_PASSWORD` must be defined.

The create the database execute these commands and replace `<user>` and `<password>`
with your values: 
 
```sh
# start psql
sudo -u postgres psql

CREATE USER "<user>" WITH PASSWORD "<password>";
CREATE DATABASE "parkapi2" ENCODING=UTF8 OWNER="<user>";
CREATE DATABASE "parkapi2-test" ENCODING=UTF8 OWNER="<user>";

# connect to each database and enable postgis
\c parkapi2
CREATE EXTENSION postgis;

\c parkapi2-test
CREATE EXTENSION postgis;
```

### Run local server and unittests 

In the `web/` directory call:

```shell script
# run unittests
./manage.py test --keepdb

# run unittests using external web APIs, e.g. Nominatim
PA_TEST_EXTERNAL_API=1 ./manage.py test --keepdb

# init the main database
./manage.py migrate
./manage.py createsuperuser

# start the server in debug mode
DJANGO_DEBUG=True ./manage.py runserver
```

By default, the django admin interface is available at 
[localhost:8000/admin/](http://localhost:8000/admin/) and the 
swagger api documentation is at
[localhost:8000/api/docs/](http://localhost:8000/api/docs/) and
a simple *developmental* overview page at [localhost:8000/](http://localhost:8000/). 


To get data into the database call:

```shell script
./manage.py pa_scrape scrape

# attach city names to new lots
./manage.py pa_find_locations
```

