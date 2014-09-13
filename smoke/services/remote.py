# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import subprocess

from django.conf import settings
from smoke.services.parsers import ApplicationMasterLaunchedParser, \
    TaskFinishedWithProgressParser, MessageFromShellParser


logger = logging.getLogger(__name__)


#==============================================================================
# Base class for executing commands through ssh
#==============================================================================

class BaseRemoteCommand(object):
    """Base class for remote commands"""

    def __init__(self, message_service, cookie):
        self.message_service = message_service
        self.cookie = cookie

        self.line_parsers = (
            ApplicationMasterLaunchedParser(self.message_service, self.cookie),
            TaskFinishedWithProgressParser(self.message_service, self.cookie),
            MessageFromShellParser(self.message_service, self.cookie),
        )

    def _process_incoming_line(self, cookie, subline):
        """Process a line of the spark-shell output.
        Pass the line to each of the existing parsers
        """

        # At this point, 'subline' was logged (ie: will appear
        #  on celery worker console or log file

        for parser in self.line_parsers:

            try:
                handled = parser.parse(subline)
                if handled:
                    return

            except Exception as e:
                logger.exception("Exception detected when handling")

                self.message_service.log_and_publish_error(
                    "Exception detected when handling line: %s",
                    e, errorLine=True)

        #------------------------------------------------------------
        # It's a normal, plain line. Any parser handled the line
        #------------------------------------------------------------
        self.message_service.publish_message(line=subline,
                                             lineIsFromRemoteOutput=True)
        return

    def _popen(self, *args, **kwargs):
        """Executes subprocess.Popen

        :returns: process
        """

        self.message_service.log_and_publish(
            "{0}: subprocess.Popen(%s)".format(self.__class__.__name__),
            args
        )

        try:
            process = subprocess.Popen(*args, **kwargs)
            return process
        except:
            self.message_service.publish_message(
                line="{0}: Popen() failed".format(
                    self.__class__.__name__))
            self.message_service.publish_message(
                line="{0}:  + SSH_CMD: '{1}'"
                "".format(self.__class__.__name__, settings.SSH_BASE_ARGS))
            self.message_service.publish_message(
                line="{0}:  + ARGS: '{1}'".format(self.__class__.__name__,
                                                  args))
            raise(Exception("{0}: Popen() failed".format(
                self.__class__.__name__)))

    def _popen_and_communicate(self, *args, **kwargs):
        """Executes subprocess.Popen + communicate()

        :param std_input: contents to send to subprocess STDIN

        :returns: process, stdout_data, stderr_data
        """

        std_input = kwargs.pop('std_input', None)

        p = self._popen(*args, **kwargs)

        try:
            stdout_data, stderr_data = p.communicate(input=std_input)
            return p, stdout_data, stderr_data

        except:
            logger.exception("%s: process.communicate() failed",
                             self.__class__.__name__)
            self.message_service.publish_message(
                line="{0}: process.communicate() failed".format(
                    self.__class__.__name__))
            raise(Exception("{0}: process.communicate() failed".format(
                self.__class__.__name__)))

    def _check_exit_status(self, process, stdout_data, stderr_data):

        if process.returncode == 0:
            return

        self.message_service.publish_message(
            line="ERROR: {0} failed! Exit status: {1}".format(
                self.__class__.__name__, process.returncode))
        self.message_service.publish_message(line="===== STDOUT =====")
        for line in stdout_data.splitlines():
            self.message_service.publish_message(line=line)
        self.message_service.publish_message(line="===== STDERR =====")
        for line in stderr_data.splitlines():
            self.message_service.publish_message(line=line)

        logger.error("{0}: exit status != 0.".format(self.__class__.__name__))
        logger.error("{0}: exit status: %s".format(self.__class__.__name__),
                     process.returncode)
        logger.error("{0}: STDOUT: %s".format(self.__class__.__name__),
                     stdout_data)
        logger.error("{0}: STDERR: %s".format(self.__class__.__name__),
                     stderr_data)

        raise(Exception("{0}: exit status != 0"
                        "".format(self.__class__.__name__)))

    def _process_stdout(self, proc):
        first_line = True
        while True:
            line = proc.stdout.readline()
            # TODO: why sublines? to facilitate regexes!
            for subline in [sl.rstrip()
                            for sl in line.splitlines() if sl.strip()]:

                logger.info("%s> %s", self.__class__.__name__, subline)

                if first_line:
                    first_line = False
                    self.message_service.log_and_publish(
                        "The first line was received", sparkStarted=True)

                self._process_incoming_line(self.cookie, subline)

            if not line:
                # this works because empty lines are '\n' and so
                # dont resovle to False
                break

        self.message_service.log_and_publish(
            "Waiting for the child to join...")

        proc.wait()

        self.message_service.log_and_publish(
            "{0}: job ended. exit_status: %s".format(self.__class__.__name__),
            proc.returncode,
            jobFinishedOk=True,
            exitStatus=proc.returncode
        )

        return proc.returncode


#==============================================================================
# Remote commands
#==============================================================================

class MkTemp(BaseRemoteCommand):
    """Remote command to create a temporary file"""

    def __init__(self, message_service, cookie):
        super(MkTemp, self).__init__(message_service, cookie)

    def mktemp(self):
        """Creates a temporary file on the remote server"""
        self.message_service.log_and_publish("Executing mktemp in "
                                             "remote server")

        ARGS = settings.SSH_BASE_ARGS + ["mktemp", "-t",
                                         "spark-job-script-XXXXXXXXXX",
                                         "--suffix=.scala"]

        proc, stdout_data, stderr_data = self._popen_and_communicate(
            ARGS,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        self._check_exit_status(proc, stdout_data, stderr_data)

        temp_file = stdout_data.splitlines()[0].strip()
        if not len(temp_file):
            self.message_service.publish_message(
                line="ERROR: mktemp:  failed! Temporary filename is empty")
            raise(Exception("Temporary filename is empty"))

        self.message_service.log_and_publish("Temporary file: %s", temp_file)
        return temp_file


class SendScript(BaseRemoteCommand):

    def __init__(self, message_service, cookie):
        super(SendScript, self).__init__(message_service, cookie)
        self.mktemp_service = MkTemp(message_service, cookie)

    def send_script(self, script):
        """Sube script a servidor.

        :returns: Path al archivo donde fue subido el script
        """
        self.message_service.log_and_publish("Sending script to server")

        temp_file = self.mktemp_service.mktemp()

        ARGS = settings.SSH_BASE_ARGS + ["cat > {0}".format(temp_file)]

        proc, stdout_data, stderr_data = self._popen_and_communicate(
            ARGS,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            std_input=script
        )

        self._check_exit_status(proc, stdout_data, stderr_data)

        self.message_service.log_and_publish("Script contents were sent "
                                             "successfully")

        return temp_file


class RunSparkShell(BaseRemoteCommand):

    def __init__(self, message_service, cookie):
        super(RunSparkShell, self).__init__(message_service, cookie)

    def run_spark_shell(self, script_path):
        """Ejecuta script spark en servidor.

        :returns: exit status of subprocess
        """
        logger.info("Ejecutando script en server: %s", script_path)

        REMOTE_COMMAND_TEMPLATE = \
            "'" + \
            "{spark_shell} " + \
            "{spark_shell_opts} " + \
            "--master yarn-client " + \
            "-i {script_path} 2>&1" + \
            "'"

        REMOTE_COMMAND = REMOTE_COMMAND_TEMPLATE.format(
            spark_shell=settings.REMOTE_SPARK_SHELL_PATH,
            script_path=script_path,
            spark_shell_opts=settings.REMOTE_SPARK_SHELL_PATH_OPTS,
        )

        self.message_service.log_and_publish("Using cookie: %s", self.cookie)

        ARGS = settings.SSH_BASE_ARGS + ["env",
                                         "DATATSUNAMI_COOKIE=" + self.cookie,
                                         "sh", "-c", REMOTE_COMMAND]

        p = self._popen(ARGS, stdout=subprocess.PIPE)

        return self._process_stdout(p)


class Cat(BaseRemoteCommand):

    def __init__(self, message_service, cookie):
        super(Cat, self).__init__(message_service, cookie)

    def run_cat(self, script_path):
        """Does a 'cat' of the script on the server.

        :returns: exit status of subprocess
        """

        #
        # FIXME: this is a copy-n-paste of _remote_spark_shell()
        #

        logger.info("Executing 'cat' (on server) of %s", script_path)

        ARGS = settings.SSH_BASE_ARGS + ["cat", script_path]

        p = self._popen(ARGS, stdout=subprocess.PIPE)

        return self._process_stdout(p)


class Echo(BaseRemoteCommand):

    def __init__(self, message_service, cookie):
        super(Echo, self).__init__(message_service, cookie)

    def remote_echo(self):
        """Does a 'echo pong' on the server.

        :returns: exit status of subprocess
        """

        #
        # FIXME: this is a copy-n-paste of _remote_spark_shell()
        #

        logger.info("Executing 'echo pong' (on server)")

        ARGS = settings.SSH_BASE_ARGS + ["echo", "pong"]

        p = self._popen(ARGS, stdout=subprocess.PIPE)

        return self._process_stdout(p)
