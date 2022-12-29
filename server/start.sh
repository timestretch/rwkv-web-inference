#!/bin/sh

export FLASK_APP=./app.py

flask --debug run -h 0.0.0.0 -p 8080
