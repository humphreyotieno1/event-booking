#!/bin/bash

# Exit on any error
set -e

echo "Starting Event Booking API..."

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Collect static files (if needed)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 120 --keep-alive 2 app.wsgi:application
