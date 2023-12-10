cd web

# Run migration only if explicitly set via ENV
if [ "$RUN_MIGRATION" != "false" ]; then
	./manage.py migrate
fi

if [ "$ASSING_LOCATIONS" != "false" ]; then
	./manage.py pa_find_locations
fi

# don't create an admin interface per default
#./manage.py createsuperuser  

# start the server
./manage.py $@
