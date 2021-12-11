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

Follow the 
[instructions](https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/postgis/) 
for installing postgres and the `postgis` extension.

Alternatively, you can run the 
[postgis docker image](https://github.com/postgis/docker-postgis):
```shell script
docker run --name some-postgis -e POSTGRES_PASSWORD=pass -d postgis/postgis
```

Then create and setup database
 
```shell script
# start psql
sudo -u postgres psql

CREATE USER "park_api" WITH PASSWORD 'park_api';
CREATE DATABASE "parkapi2" ENCODING=UTF8 OWNER="park_api";

# allow park_api user to create the unittest database and 
# enable the postgis extension  
ALTER USER "park_api" SUPERUSER;
```

> Note that `ALTER USER "park_api" CREATEDB;` is usually enough for 
> running the unittests but the `postgis` extension 
> [can only be enabled by a superuser](https://dba.stackexchange.com/questions/175319/postgresql-enabling-extensions-without-super-user/175469#175469).

Then in the `web/` directory call:

```shell script
# run unittests
./manage.py test

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
a simple overview page at [localhost:8000/](http://localhost:8000/). 


To get data into the database call:

```shell script
./manage.py pa_scrape scrape

# attach city names to new lots
./manage.py pa_find_locations
```


## Docker and CI

The [Dockerfile](Dockerfile) is an Ubuntu based image. It's probably possible
to switch to Alpine but the postgis libraries are currently not working in 
my attempts.

```shell script
docker build --tag parkapi-dev .
```

#### run unittests in docker container

```shell script
docker run -ti --env PARKAPI_RUN_TESTS=1 --net host parkapi-dev
```

Running the container with `--net host` will attach to the postgres at localhost. Please
check the example in the 
[postgis docker README](https://github.com/postgis/docker-postgis#readme)
how to connect to a different host. 

#### running the server in docker container

```shell script
docker run -ti --env DJANGO_DEBUG=True --net host parkapi-dev
```

Running in non-DEBUG mode will not deliver static files as this
requires a webserver like nginx or apache.
