#!/usr/bin/env sh

# better to use another entrypoint
python manage.py makemigrations
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "Migration failed." >&2
    exit 1
fi

# todo: maybe we don't need it
python insert_init_data.py

if [[ $# -gt 0 ]]; then
    INPUT=$@
    sh -c "$INPUT"
else
    python ./manage.py collectstatic --noinput
    echo "Starting Gunicorn..."
    gunicorn core.wsgi --bind 0.0.0.0:8000 --timeout 1000 -w 5 --reload
fi

