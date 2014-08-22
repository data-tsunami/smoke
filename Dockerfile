#
# To build de Docker image:
#
#     $ docker build -t data-tsunami.com/spark-web-ui .
#
# To run interactively (so you can see the logs):
#
#     $ docker run -ti -p 8989:8080 data-tsunami.com/spark-web-ui
#

FROM ubuntu:14.04

MAINTAINER Horacio G. de Oro <hgdeoro@gmail.com>

RUN apt-get update
RUN apt-get install -y python-django redis-server python-virtualenv
RUN apt-get install -y python-dev
RUN apt-get install -y libssl-dev openssh-client

ADD requirements.txt /tmp/requirements.txt
RUN virtualenv -p python2.7 /tmp/virtualenv
RUN /tmp/virtualenv/bin/pip install -r /tmp/requirements.txt

ADD manage.py /tmp/manage.py
ADD run_uwsgi.sh /tmp/run_uwsgi.sh
ADD web /tmp/web

ADD web_settings_local.py /tmp/web_settings_local.py

ENV RUNNIN_IN_DOCKER 1

RUN cd /tmp ; \
	/tmp/virtualenv/bin/python manage.py syncdb --noinput ; \
	/tmp/virtualenv/bin/python manage.py migrate

CMD ["/tmp/run_uwsgi.sh"]
