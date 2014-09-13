# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import re
from xml.dom.minidom import parseString


logger = logging.getLogger(__name__)

RE_APPLICATION_MASTER_LAUNCHED = re.compile(r"^\S+\s\S+\sINFO\s"
                                            "yarn\.Client:\sCommand\sfor\s"
                                            "starting\sthe\sSpark\s"
                                            "ApplicationMaster")
"""14/08/19 16:07:31 INFO yarn.Client: \
   Command for starting the Spark ApplicationMaster: \
   List(...)
"""

RE_TASK_FINISHED_WITH_PROGRESS = re.compile(r""
                                            "^.*"
                                            "INFO\s+"
                                            "scheduler\.TaskSetManager:\s+"
                                            "Finished\s+TID\s+"
                                            "(\d+)\s+"
                                            "in\s+"
                                            "(\d+)\s+"
                                            "ms\s+"
                                            "on\s+"
                                            "(.+)\s+"
                                            "\("
                                            "progress:\s+"
                                            "(\d+)/(\d+)"
                                            "\)"
                                            )
""" 14/08/19 17:02:15 INFO scheduler.TaskSetManager: \
    Finished TID 24 in 3386 ms on xxxxxxxxx (progress: 26/70)
"""

RE_MESSAGE_FROM_SHELL = re.compile(r"^@@(.+)@@$")


#------------------------------------------------------------
# RE_APPLICATION_MASTER_LAUNCHED
#------------------------------------------------------------

class ApplicationMasterLaunchedParser(object):

    def __init__(self, message_service, cookie):
        self.message_service = message_service
        self.cookie = cookie

    def parse(self, subline):
        """Parses the line.

        :returns: True if the line was parsed and handled
        """

        if not RE_APPLICATION_MASTER_LAUNCHED.search(subline):
            return False

        self.message_service.log_and_publish(subline,
                                             lineIsFromRemoteOutput=True,
                                             appMasterLaunched=True)
        return True


#------------------------------------------------------------
# RE_TASK_FINISHED_WITH_PROGRESS
#------------------------------------------------------------

class TaskFinishedWithProgressParser(object):

    def __init__(self, message_service, cookie):
        self.message_service = message_service
        self.cookie = cookie

    def parse(self, subline):
        """Parses the line.

        :returns: True if the line was parsed and handled
        """

        progress_match = RE_TASK_FINISHED_WITH_PROGRESS.search(subline)
        if not progress_match:
            return False

        # tid_id = progress_match.group(1)
        # took = progress_match.group(2)
        # host = progress_match.group(3)
        progress_done = progress_match.group(4)
        progress_total = progress_match.group(5)
        self.message_service.log_and_publish(subline,
                                             lineIsFromRemoteOutput=True,
                                             progressUpdate=True,
                                             progressDone=int(progress_done),
                                             progressTotal=int(progress_total))

        return True


#------------------------------------------------------------
# RE_MESSAGE_FROM_SHELL
#------------------------------------------------------------

class MessageFromShellParser(object):

    def __init__(self, message_service, cookie):
        self.message_service = message_service
        self.cookie = cookie

    def parse(self, subline):
        """Parses the line.

        :returns: True if the line was parsed and handled
        """

        msg_from_shell = RE_MESSAGE_FROM_SHELL.search(subline)
        if not msg_from_shell:
            return False

        maybe_xml = msg_from_shell.group(1)

        #======================================================================
        # Parse XML
        #======================================================================

        try:
            # FIXME: parseString() is insecure
            root = parseString(maybe_xml)

        except Exception as e:
            logger.exception("Parsing XML failed")

            self.message_service.log_and_publish("Exception detected when "
                                                 "tryed to parse line from "
                                                 "shell: %s", e,
                                                 errorLine=True)

            # TODO: the previouws line must be logged as error
            return False

        #======================================================================
        # Handle XML
        #======================================================================

        try:
            return self._process_xml(subline, root)

        except Exception as e:
            logger.exception("Handling XML failed")

            self.message_service.log_and_publish("Exception detected when "
                                                 "trying to handle XML from "
                                                 "line from shell: %s",
                                                 e, errorLine=True)

            # TODO: the previouws line must be logged as error
            return False

    def _process_xml(self, subline, root):

        cookie_from_xml = root.getElementsByTagName(
            'msgFromShell')[0].attributes['cookie'].value

        # Check cookie
        if cookie_from_xml != self.cookie:
            # BAD COOKIE!
            self.message_service.log_and_publish(
                "ERROR: cookies doesn't matches. "
                "Cookie: %s - From XML: %s",
                self.cookie,
                cookie_from_xml,
                lineIsFromRemoteOutput=True,
                errorLine=True)
            # TODO: the previouws line must be logged as error
            return False

        # Check <errorLine>
        try:
            errors = root.getElementsByTagName('errorLine')
            assert errors
        except:
            pass
        else:
            for elem in errors:
                error_line = elem.firstChild.data.rstrip()
                self.message_service.log_and_publish(
                    error_line,
                    lineIsFromRemoteOutput=True,
                    errorLine=True)
            return True

        # Check <outputFileName>
        try:
            output_filename = root.getElementsByTagName(
                'outputFileName')[0].firstChild.data.strip()
        except:
            pass
        else:
            self.message_service.log_and_publish(
                subline,
                lineIsFromRemoteOutput=True,
                outputFilenameReported=output_filename)
            return True

        # UNKNOW <msgFromShell> TYPE
        self.message_service.log_and_publish("ERROR: unknown type of line "
                                             "from shell: %s",
                                             subline, errorLine=True)
        # TODO: the previouws line must be logged as error
        return False
