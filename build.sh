#!/usr/bin/env bash
# Build script for Render deployment

# Exit on any error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate

# Create superuser if it doesn't exist (optional, for initial setup)
# python manage.py createsuperuser --noinput || true

echo "Build completed successfully!"
