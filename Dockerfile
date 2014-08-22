#
# BUILD:
#     $ docker build -t data-tsunami.com/spark-web-ui .
#

FROM ubuntu:14.04

MAINTAINER Horacio G. de Oro <hgdeoro@gmail.com>

RUN apt-get update
RUN apt-get install -y python-django redis-server python-virtualenv
RUN apt-get install -y python-dev

ADD requirements.txt /tmp/requirements.txt
RUN virtualenv -p python2.7 /tmp/virtualenv
RUN /tmp/virtualenv/bin/pip install -r /tmp/requirements.txt

ADD manage.py /tmp/manage.py
ADD run_uwsgi.sh /tmp/run_uwsgi.sh
ADD web /tmp/web

ADD web_settings_local.py /tmp/web_settings_local.py

ENV RUNNIN_IN_DOCKER 1
