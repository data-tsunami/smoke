Spark UI
========

Web interface to execute Scala jobs in Spark.

Requires passwordless connection to the cluster using `ssh` (for launching the job). Uses `spark-shell` in `yarn client` mode.

![Architecture](/architecture.png?raw=true)

Configuration
-------------

* `SSH_BASE_ARGS`: this should be an array with the commands and arguments to connect
  to the server. That server must have Spark installed and `spark-shell` working.

Example:

    SSH_BASE_ARGS = ["ssh", "-o", "StrictHostKeyChecking=no",
        "hadoop@cluster-master.hadoop.dev.docker.data-tsunami.com"]


Requires
--------

* Python 2.7
* Hadoop 2.4.1
* Spark 1.0.2

Next steps
----------

* Load Spark results on IPython Notebook
* Kill running jobs
* Better integratoin with Yarn API

TODO
----

* Add utilities
* Refactor parser of console output
* Refactor actions to reuse code
* Evaluate paramiko instead of Popen + ssh. See: http://www.paramiko.org/
* Evaluate 'load'. See: https://github.com/apache/spark/blob/master/repl/src/main/scala/org/apache/spark/repl/SparkILoop.scala
* Docker: use non-root user
* Docker: mount SQlite database in volume

Licence
-------

    #===============================================================================
    #    SparkUI - Launch Spark jobs from the web
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

