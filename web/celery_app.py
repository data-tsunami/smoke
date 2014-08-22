# -*- coding: utf-8 -*-
"""
Defines the Celery app.
"""

from __future__ import absolute_import
from __future__ import unicode_literals

from celery import Celery
from django.conf import settings
import logging as _logging


logger = _logging.getLogger('web.celery_app')

app = Celery('tasks')

app.config_from_object('django.conf:settings')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    CELERY_ROUTES={
        'web.tasks.spark_job': {
            'queue': 'spark_job'
        },
    },
)
#
# if __name__ == '__main__':
#     logger.info("Starting Celery daemon...")
#     app.start()
