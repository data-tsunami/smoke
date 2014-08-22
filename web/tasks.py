# -*- coding: utf-8 -*-
"""
Tasks to be run in the Celery workers.
"""

from __future__ import unicode_literals

import logging

from web import celery_app
from web.spark_job import SparkService, MessageService


logger = logging.getLogger(__name__)


@celery_app.app.task(ignore_result=True)
def spark_job(script, action):
    """Launch a job. Sincrhronous version."""
    SparkService().launc_job(script, action)


def spark_job_async(script, action):
    """Launches a job asynchronously on Celery"""
    logger.info("Launching Celery asynchronous job - action: %s", action)

    message_service = MessageService()
    message_service.publish_message("Scheduling async execution of script",
                                    jobSubmitted=True)

    # Log the script
    for line in script.splitlines():
        logger.info("# {0}".format(line.strip()))

    return spark_job.delay(script, action)
