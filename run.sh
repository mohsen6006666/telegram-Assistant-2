#!/bin/bash

# Start Flask server for health check
echo "Starting Flask server for health check..."
gunicorn --bind 0.0.0.0:5000 --config gunicorn_config.py app:app