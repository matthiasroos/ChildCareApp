#!/bin/bash

gunicorn --workers=2 -k uvicorn.workers.UvicornWorker -b localhost:8085 backend.app.REST.starlite.server:app
