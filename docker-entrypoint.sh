# #!/usr/bin/env sh

if [ "$ENVIRONMENT" = "development" ]; then
    python manage.py makemigrations || {
        echo "Makemigrations failed"
        exit 1
    }
fi

python manage.py migrate

if [ $? -ne 0 ]; then
    echo "Migration failed." >&2
    exit 1
fi

if [ "$ENVIRONMENT" = "development" ]; then
    echo "Loading initial data..."
    python manage.py loaddata data.json || {
        echo "Loading json data failed"
        exit 1
    }
    python insert_init_data.py
fi

echo "Starting Gunicorn..."
gunicorn core.wsgi --bind 0.0.0.0:8000 --timeout 1000 -w 5 --reload
