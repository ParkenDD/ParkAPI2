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
or use the [web interface](https://nominatim.openstreetmap.org/ui/search.html).
To view the details of an ID use 
[the detail page](https://nominatim.openstreetmap.org/ui/details.html).


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

````
# run unittests
./manage.py test

# or start the server
./manage.py createsuperuser
./manage.py runserver
```
