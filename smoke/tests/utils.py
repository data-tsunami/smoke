# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class MessageServiceMock(object):
    """Mock of MessageService"""

    def __init__(self):
        self.messages = []

    def publish_message(self, line, **kwargs):
        self.messages.append((line, kwargs))

    def log_and_publish(self, message, *args, **kwargs):
        self.messages.append((message, args, kwargs))

    def log_and_publish_error(self, message, *args, **kwargs):
        self.messages.append((message, args, kwargs))

    def get_log(self):
        pass
