echo "Make migrations"
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py makemigrations kinksorter_app
python manage.py migrate

python manage.py qcluster &

echo "Start Gunicorn"
gunicorn kinksorter.wsgi:application --bind 0.0.0.0:8080
