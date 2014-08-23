#!/bin/bash

NAME="spark_job"

export DJANGO_SETTINGS_MODULE=smoke.settings

celery \
	-A smoke.celery_app.app \
        -Q ${NAME} \
	--no-color \
	--loglevel=info \
	--concurrency=1 \
	--pidfile=/tmp/.datatsunami-sparkui-celery-worker--${NAME}.pid \
	worker \
	$*
exit $?

