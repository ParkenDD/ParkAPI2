# init the main database
cd /app/web
./manage.py migrate

# don't create an admin interface per default
#./manage.py createsuperuser  

# start the server
./manage.py $@
