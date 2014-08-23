# Smoke - Web interface for Spark

Web interface to execute Scala jobs in Spark.

Requires passwordless connection to the cluster using `ssh` (for launching the job). Uses `spark-shell` in `yarn client` mode.

![Architecture](/architecture.png?raw=true)


## Download and run

###### Step 1: Clone this repo and enter into it

    $ git clone https://github.com/data-tsunami/smoke
    $ cd smoke

###### Step 2: Create the virtualenv and install requirements.txt

    $ virtualenv -p python2.7 virtualenv
    $ ./virtualenv/bin/pip install -r requirements.txt

###### Step 3: Configure (you'll find the instructions in web_settings_local_SAMPLE.py)

    $ cp web_settings_local_SAMPLE.py web_settings_local.py
    $ vim web_settings_local.py

###### Step 4: Run:

    $ ./run_uwsgi.sh

This script will run Django's `syncdb`, `migrate` and `collectstatic`. Then will start `uWSGI` and the `Celery` worker.

Go to [http://localhost:8077/](http://localhost:8077/) and enjoy!


## Requirements

Smoke is developed and tested with:

* Python 2.7
* Hadoop 2.4.1
* Spark 1.0.2
* Redis
* Ubuntu 14.04, with at least:
  * python-dev
  * libssl-dev
  * openssh-client
  * python-virtualenv



## FAQ and troubleshooting

###### Make uWSGI listen in other address/port

Use the environment variable `SMOKE_UWSGI_HTTP`. For example:

    $ env SMOKE_UWSGI_HTTP=127.0.0.1:7777 ./run_uwsgi.sh

###### ERROR: Cannot connect to redis://127.0.0.1:6379/4

You get a lot of this in your console:

    [2014-08-22 23:44:02,232: ERROR/MainProcess] consumer: Cannot connect to redis://127.0.0.1:6379/4: Error 111 connecting to 127.0.0.1:6379. Connection refused..
    Trying again in 2.00 seconds...

Install and start Redis! On Ubuntu 14.04, you must run:

    $ sudo apt-get install -y redis-server
    $ sudo service redis-server start


###### ERROR: you need to build uWSGI with SSL support to use the websocket handshake api function

You forgot install the required packages. Install `libssl-dev` and reinstall the `virtualenv` requirements.

###### Run in Docker

If you are brave enough, see instructions at [Dockerfile!](Dockerfile).

## Next steps

* Load Spark results on IPython Notebook
* Kill running jobs
* Better integratoin with Yarn API


## TODO


* Add Scala utilities
* Refactor parser of console output
* Refactor actions to reuse code
* Evaluate paramiko instead of Popen + ssh. See: http://www.paramiko.org/
* Evaluate 'load'. See: https://github.com/apache/spark/blob/master/repl/src/main/scala/org/apache/spark/repl/SparkILoop.scala
* Docker: mount SQlite database in volume


## Licence

    #===============================================================================
    #    Smoke - Launch Spark jobs from the web
    #
    #    Copyright (C) 2014 Horacio Guillermo de Oro <hgdeoro@gmail.com>
    #
    #    This program is free software: you can redistribute it and/or modify
    #    it under the terms of the GNU General Public License as published by
    #    the Free Software Foundation, either version 3 of the License, or
    #    (at your option) any later version.
    #
    #    This program is distributed in the hope that it will be useful,
    #    but WITHOUT ANY WARRANTY; without even the implied warranty of
    #    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #    GNU General Public License for more details.
    #
    #    You should have received a copy of the GNU General Public License
    #    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    #===============================================================================

