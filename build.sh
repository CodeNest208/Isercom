#!/usr/bin/env bash
# build.sh - Render build script

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

# Collect static files (including frontend files)
python manage.py collectstatic --no-input --clear

# Run database migrations
python manage.py migrate
