#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Start Redis
redis-server &

# Start the RQ worker in the background
rq worker &

# Start the Flask application
python app.py
