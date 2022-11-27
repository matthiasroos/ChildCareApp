#!/bin/bash

gunicorn -w 2 'server_flask:app'