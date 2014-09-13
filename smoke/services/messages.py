# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
from logging import LogRecord
import logging

from django.conf import settings
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage


logger = logging.getLogger(__name__)


class MessageService(object):
    """Service to handle messages, including local
    logging and publishing using Redis.
    """

    def __init__(self):
        self._redis_publisher = RedisPublisher(
            facility=settings.REDIS_PUBLISHER_FACILITY_LABEL,
            broadcast=True)
        self._log_lines = []

    def publish_message(self, line, **kwargs):
        """Publishes a messages using Redis. This line is sent to
        the web.

        The line could be an empty string
        """
        # Line could be an empty string: in case we need to inform
        # some situation to the web tier, we send a dict with flags,
        # but we don't want to send a log line.
        if line:
            self._log_lines.append(line)

        message_dict = {'line': line}
        message_dict.update(kwargs)

        self._redis_publisher.publish_message(
            RedisMessage(json.dumps(message_dict)))

    def log_and_publish(self, message, *args, **kwargs):
        """Log a line using and publish it to the web tier.

        The *args are passed to logger.info()
        The **kwargs are passed to '_send_line()'
        """
        logger.info(message, *args)
        record = LogRecord('name', logging.INFO, "(unknown file)", 0,
                           message, args, exc_info=None, func=None)
        full_message = record.getMessage()
        self.publish_message(line=full_message, **kwargs)
        # self._log_lines.append(message)

    def log_and_publish_error(self, message, *args, **kwargs):
        """Log a line using and send it to the web tier.
        The *args are passed to logger.info()
        The **kwargs are passed to '_send_line()'
        """
        logger.error(message, *args)
        record = LogRecord('name', logging.ERROR, "(unknown file)", 0,
                           message, args, exc_info=None, func=None)
        full_message = record.getMessage()
        updated_kwargs = dict(kwargs)
        updated_kwargs['errorLine'] = True
        self.publish_message(line=full_message, **updated_kwargs)
        # self._log_lines.append(message)

    def get_log(self):
        """Returns the saved log lines as a single string"""
        return "\n".join(self._log_lines)
