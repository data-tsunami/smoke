# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import uuid

from django.test import TestCase
from smoke.services.parsers import ApplicationMasterLaunchedParser, \
    TaskFinishedWithProgressParser, MessageFromShellParser
import pprint

GENERAL_INVALID_LINES = (

    # empty line
    "",

    # line with some characters
    "xxxxxx",

    # a real line, but any parser handles it
    ("14/08/23 12:48:53 INFO scheduler.DAGScheduler: "
     "Completed ShuffleMapTask(1, 0)")

)


class MessageServiceMock(object):

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


class TestApplicationMasterLaunchedParser(TestCase):

    def test(self):
        cookie = uuid.uuid4().hex
        msg_service = MessageServiceMock()
        parser = ApplicationMasterLaunchedParser(msg_service, cookie)

        # TODO: get real line from real execution to test this
        LINE = ("xxx xxx INFO yarn.Client: Command for "
                "starting the Spark ApplicationMaster")

        for invalid_line in GENERAL_INVALID_LINES:
            self.assertFalse(parser.parse(invalid_line))

        self.assertTrue(parser.parse(LINE))

        appMasterLaunched = [item.get('appMasterLaunched', False)
                             for sublist in msg_service.messages
                             for item in sublist
                             if isinstance(item, dict)]

        self.assertIn(True, appMasterLaunched)


class TestTaskFinishedWithProgressParser(TestCase):

    def test(self):
        cookie = uuid.uuid4().hex
        msg_service = MessageServiceMock()
        parser = TaskFinishedWithProgressParser(msg_service, cookie)

        LINE = ("14/08/23 12:48:53 INFO "
                "scheduler.TaskSetManager: "
                "Finished TID 0 in 7443 ms on "
                "hadoop-hitachi80gb.hadoop.dev.docker.data-tsunami.com "
                "(progress: 4/10)")

        for invalid_line in GENERAL_INVALID_LINES:
            self.assertFalse(parser.parse(invalid_line))

        self.assertTrue(parser.parse(LINE))

        progressUpdate = [item.get('progressUpdate', False)
                          for sublist in msg_service.messages
                          for item in sublist
                          if isinstance(item, dict)]

        self.assertIn(True, progressUpdate)


class TestMessageFromShellParser(TestCase):

    def test_invalid_lines(self):
        cookie = uuid.uuid4().hex
        msg_service = MessageServiceMock()
        parser = MessageFromShellParser(msg_service, cookie)

        INVALID_LINES = (
            "@@@@",
            "@@some text@@",
            "@@<some_xml></some_xml>@@",
            "@@<msgFromShell></msgFromShell>@@",
            "@@<msgFromShell><errorLine>ERR</errorLine></msgFromShell>@@",
        )

        # -----

        for invalid_line in GENERAL_INVALID_LINES:
            self.assertFalse(parser.parse(invalid_line))

        for invalid_line in INVALID_LINES:
            self.assertFalse(parser.parse(invalid_line))

    def test_wrong_cookie(self):
        cookie = uuid.uuid4().hex
        wrong_cookie = uuid.uuid4().hex
        msg_service = MessageServiceMock()
        parser = MessageFromShellParser(msg_service, cookie)

        WRONG_COOKIE = ("@@"
                        "<msgFromShell cookie='{0}'>"
                        "<errorLine>This is the line</errorLine>"
                        "</msgFromShell>"
                        "@@".format(wrong_cookie))

        # -----

        self.assertFalse(parser.parse(WRONG_COOKIE))

    def test_errorLine(self):
        cookie = uuid.uuid4().hex
        msg_service = MessageServiceMock()
        parser = MessageFromShellParser(msg_service, cookie)

        error_msg = "This-is-the-line-" + uuid.uuid4().hex
        LINE = ("@@"
                "<msgFromShell cookie='{0}'>"
                "<errorLine>{1}</errorLine>"
                "</msgFromShell>"
                "@@".format(cookie,
                            error_msg))

        # -----

        self.assertTrue(parser.parse(LINE))

        error_msg_found = [error_msg == item
                           for sublist in msg_service.messages
                           for item in sublist]

        self.assertIn(True, error_msg_found)
