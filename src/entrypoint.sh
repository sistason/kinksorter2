#!/bin/bash

echo "Make migrations"
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py makemigrations kinksorter_app
python manage.py migrate

if [[ "$#" -ne 0 ]]; then
    echo "Run command $1"
    python manage.py $@
else
    echo "Start Gunicorn"
    python manage.py qcluster &
    exec gunicorn kinksorter.wsgi:application --bind 0.0.0.0:8080
fi