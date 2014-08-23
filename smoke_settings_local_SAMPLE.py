
#
# Django settings
#

DEBUG = False
TEMPLATE_DEBUG = False

ALLOWED_HOSTS = '*'

#
# Smoke settings
#

#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
#   You must configure `SSH_BASE_ARGS`
#                                       (and maybe `REMOTE_SPARK_SHELL_PATH`)
#
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
#
# The 'SSH_BASE_ARGS' is used to execute commands in the remote server.
# The remote server must have Spark installed and configured, and the
#  `spark-shell` on `$SPARK_PREFIX/bin/spark-shell` will be used by default.
#
# For example, if you run the following command to launch a
#  Spark shell from your terminal:
#
# $ ssh hadoop@10.6.10.244 /opt/spark-1.0.2/bin/spark-shell \
#    --master yarn-client
#
# then you must configure:
#
# SSH_BASE_ARGS = ["ssh", "hadoop@10.6.10.244"]
# REMOTE_SPARK_SHELL_PATH = ["/opt/spark-1.0.2/bin/spark-shell"]
#
# If in your server you have `$SPARK_PREFIX`, you don't need
#  to set `REMOTE_SPARK_SHELL_PATH`
#

SSH_BASE_ARGS = ["ssh", "-o", "StrictHostKeyChecking=no",
    "hadoop_user@hostname_or_ip_where_spark_is_installed"]
