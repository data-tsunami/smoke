# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import uuid

from django.test import TestCase
from smoke.services.parsers import ApplicationMasterLaunchedParser, \
    TaskFinishedWithProgressParser, MessageFromShellParser

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

    def publish_message(self, line, **kwargs):
        pass

    def log_and_publish(self, message, *args, **kwargs):
        pass

    def log_and_publish_error(self, message, *args, **kwargs):
        pass

    def get_log(self):
        pass


class TestApplicationMasterLaunchedParser(TestCase):

    def test(self):
        cookie = uuid.uuid4().hex
        parser = ApplicationMasterLaunchedParser(MessageServiceMock(), cookie)

        # TODO: get real line from real execution to test this
        LINE = ("xxx xxx INFO yarn.Client: Command for "
                "starting the Spark ApplicationMaster")

        for invalid_line in GENERAL_INVALID_LINES:
            self.assertFalse(parser.parse(invalid_line))

        self.assertTrue(parser.parse(LINE))


class TestTaskFinishedWithProgressParser(TestCase):

    def test(self):
        cookie = uuid.uuid4().hex
        parser = TaskFinishedWithProgressParser(MessageServiceMock(), cookie)

        LINE = ("14/08/23 12:48:53 INFO "
                "scheduler.TaskSetManager: "
                "Finished TID 0 in 7443 ms on "
                "hadoop-hitachi80gb.hadoop.dev.docker.data-tsunami.com "
                "(progress: 4/10)")

        for invalid_line in GENERAL_INVALID_LINES:
            self.assertFalse(parser.parse(invalid_line))

        self.assertTrue(parser.parse(LINE))


class TestMessageFromShellParser(TestCase):

    def test(self):
        cookie = uuid.uuid4().hex
        wrong_cookie = uuid.uuid4().hex
        parser = MessageFromShellParser(MessageServiceMock(), cookie)

        LINE = ("@@"
                "<msgFromShell cookie='{0}'>"
                "<errorLine>This is the line</errorLine>"
                "</msgFromShell>"
                "@@".format(cookie))

        WRONG_COOKIE = ("@@"
                        "<msgFromShell cookie='{0}'>"
                        "<errorLine>This is the line</errorLine>"
                        "</msgFromShell>"
                        "@@".format(wrong_cookie))

        INVALID_LINES = (
            "@@@@",
            "@@some text@@",
            "@@<some_xml></some_xml>@@",
            "@@<msgFromShell></msgFromShell>@@",
            "@@<msgFromShell><errorLine>ERR</errorLine></msgFromShell>@@",
            WRONG_COOKIE
        )

        for invalid_line in GENERAL_INVALID_LINES:
            self.assertFalse(parser.parse(invalid_line))

        for invalid_line in INVALID_LINES:
            self.assertFalse(parser.parse(invalid_line))

        self.assertTrue(parser.parse(LINE))
