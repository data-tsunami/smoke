#!/bin/bash

BASEDIR=$(cd $(dirname $0) ; pwd)

# cd to the directory to avoid problems with 
#  scripts launched with --attach-daemon=
cd $BASEDIR

if [ -z "${VIRTUAL_ENV}" -a -d ${BASEDIR}/virtualenv ] ; then
	. ${BASEDIR}/virtualenv/bin/activate
fi

if [ -z "$DISABLE_STATIC_MAP" ] ; then
	STATIC_MAP="--static-map /static=${BASEDIR}/web/dev/static_root"
	echo "Using static map arguments: $STATIC_MAP"
else
	echo "Running without --static-map."
fi

# Run collectstatics
python manage.py collectstatic  --noinput --no-post-process

# HACK: if run from Docker, start redis
if [ "$RUNNIN_IN_DOCKER" != "" ] ; then
	echo "Runnin on Docker... Will start redis"
	service redis-server start
fi

# Launch uWSGI
uwsgi \
    --module=web.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-web.settings} \
    $EXTRA_ENV \
    --master \
    --processes=${UWSGI_PROCESSES:-5} --enable-threads \
    --home=${VIRTUAL_ENV} \
    --http=${UWSGI_HTTP:-0.0.0.0:8080} \
    --uwsgi-socket=0.0.0.0:8099 \
    --python-path=${BASEDIR} \
    --master-fifo=/tmp/.datatsunami-sparkui-uwsgi-fifo \
    $STATIC_MAP \
    \
    --gevent 100 \
    --http-websockets \
    \
    --attach-daemon=${BASEDIR}/web/dev/celery_worker.sh \
    $*
