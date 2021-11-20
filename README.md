# offenesdresden/ParkAPI rewrite in Django

This is an attempt to rewrite the [ParkAPI](https://github.com/offenesdresden/ParkAPI/)
using [GeoDjango](https://docs.djangoproject.com/en/3.2/ref/contrib/gis/) and
the [django rest framework](https://www.django-rest-framework.org/).


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
> [can only be installed by a superuser](https://dba.stackexchange.com/questions/175319/postgresql-enabling-extensions-without-super-user/175469#175469).

Then in the `web/` directory call:

````
# run unittests
./manage.py test

# or start the server
./manage.py createsuperuser
./manage.py runserver
```

