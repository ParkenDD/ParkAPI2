#!/bin/bash
set -euo pipefail

cd web
if [ "$RUN_MIGRATION" -eq "1" ]; then
	echo "RUN MIGRATION is TRUE"
fi

# Run migration only if explicitly set via ENV
if [ "$RUN_MIGRATION" -eq "1" ]; then
	./manage.py migrate
fi

if [ "$ASSIGN_LOCATIONS" -eq "1" ]; then
	./manage.py pa_find_locations
fi

# don't create an admin interface per default
if [ "$CREATE_SUPERUSER" -eq "1" ]; then
	./manage.py createsuperuser
fi

# start the server
./manage.py $@
