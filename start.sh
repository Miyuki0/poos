#!/bin/bash

echo "Initializing db"
python init_db.py

echo "Starting flask"
python app.py