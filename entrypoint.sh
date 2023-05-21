#!/bin/bash

sleep 10

alembic upgrade head

celery -A src.notifications.celery_ worker --loglevel=INFO -B --pool=solo &

gunicorn src.main:app --workers 7 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80

