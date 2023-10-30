cd web

# Run migration only if explicitly set via ENV
if [ "$RUN_MIGRATION" != "false" ]; then
	./manage.py migrate
fi

# don't create an admin interface per default
#./manage.py createsuperuser  

# start the server
./manage.py $@
