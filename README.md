# offenesdresden/ParkAPI rewrite in Django

This is an attempt to rewrite the [ParkAPI](https://github.com/offenesdresden/ParkAPI/)
using [GeoDjango](https://docs.djangoproject.com/en/3.2/ref/contrib/gis/) and
the [django rest framework](https://www.django-rest-framework.org/).

## Data 

Parking lots are identified by a unique string ID. Cities, states and countries 
are identified by the 
[OpenStreetMap ID](https://wiki.openstreetmap.org/wiki/Persistent_Place_Identifier#Element.27s_OSM_ID). 

Please check the documentation in 
[web/park_data/models/_store.py](web/park_data/models/_store.py) for the 
layout of the data that needs to be supplied by a scraper.


### OSM IDs in Nominatim

Cities and larger entities are identified by the `osm_type` and `osm_id`. This
seems to be the most permanent unique mapping that is currently available 
by OpenStreetMap. More details 
[here](https://nominatim.org/release-docs/develop/api/Output/#place_id-is-not-a-persistent-id) 
and 
[here](https://wiki.openstreetmap.org/wiki/Persistent_Place_Identifier).

To find the `osm_id` for a specific place you can use the 
[Nominatim search API](https://nominatim.org/release-docs/develop/api/Search/)
or use the [web interface](https://nominatim.openstreetmap.org/ui/search.html)
to search and the [detail page](https://nominatim.openstreetmap.org/ui/details.html)
to view or validate IDs.


## Scraping

A prototype is developed in [web/scrapers/builtin/](web/scrapers/builtin/).


## Setup for development

### Clone repo and setup python environment

```
git clone https://github.com/defgsus/ParkAPI2
cd ParkAPI2

virtualenv -p python3 env
source env/bin/activate

pip install -r requirements.txt
```

### Create a postgres database

Follow the 
[instructions](https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/postgis/) 
for installing postgres and the `postgis` extension.

Alternatively, you can run the 
[postgis docker image](https://github.com/postgis/docker-postgis):
```
docker run --name some-postgis -e POSTGRES_PASSWORD=pass -d postgis/postgis
```


Then 
```
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

```
# run unittests
./manage.py test

# init the main database
./manage.py migrate
./manage.py createsuperuser

# start the server
./manage.py runserver
# or in debug mode
DJANGO_DEBUG=True ./manage.py runserver
```

By default, the admin interface is available at 
[localhost:8000/admin/](localhost:8000/admin/). 

Right now, the only thing one can do is creating Cities, States and Countries
and tie them together. E.g.

- create a new city
- type `R191645` into the OSM ID field
- press "Save and continue"
- press "Query nominatim"

It should populate the name and geo fields. 


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
check the example in the [postgis docker README](https://github.com/postgis/docker-postgis)
how to connect to a different host. 

#### running the server in docker container

```shell script
docker run -ti --env DJANGO_DEBUG=True --net host parkapi-dev
```

Running in non-DEBUG mode will not deliver static files as this
requires a webserver like nginx or apache.
