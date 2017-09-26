#!/usr/bin/env bash
rm db.sqlite3
#redis-cli FLUSHALL
find . -path "./APIs/migrations/*.pyc"  -delete
find . -path "./APIs/migrations/*.py" -not -name "__init__.py" -delete
celery -A watchMe purge -f
python manage.py makemigrations
python manage.py migrate
