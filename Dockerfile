#
# To build de Docker image
# ------------------------
#
#    1) create 'web_settings_local.py' (see web_settings_local_example.py)
#
#    2) copy the ssh keys to be used to connect to the server
#        to the 'ssh-keys' directory (I know, it's ugly! Please
#        tell me if you know a better way)
#
#    3) build the Docker image:
#
#        $ docker build -t data-tsunami.com/spark-web-ui .
#
# Launch the container
# --------------------
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

ENV RUNNIN_IN_DOCKER 1

CMD ["/tmp/run_uwsgi.sh"]

RUN useradd --home-dir /home/web web

ADD web_settings_local.py /tmp/web_settings_local.py

RUN cd /tmp ; \
	/tmp/virtualenv/bin/python manage.py syncdb --noinput ; \
	/tmp/virtualenv/bin/python manage.py migrate

ADD ssh-keys /home/web/.ssh/
RUN chown -R web.web /home/web/.ssh
RUN chmod 0700 /home/web/.ssh
