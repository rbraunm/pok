#!/bin/bash
set -e

echo "Initializing database objects..."
python -c "from api.db import initializeDbObjects; initializeDbObjects()"
echo "Database initialized. Starting Flask app."

exec gunicorn --chdir /app/web --bind 0.0.0.0:8202 app:app
