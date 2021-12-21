#!/usr/bin/env bash

./manage.py migrate || exit 1

#./manage.py compilemessages || exit 1
./manage.py collectstatic --no-input || exit 1

gunicorn -b 127.0.0.1:8000 park_api.wsgi || exit 1
