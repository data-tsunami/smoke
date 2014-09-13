# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import subprocess

from django.conf import settings
from smoke.services.parsers import ApplicationMasterLaunchedParser, \
    TaskFinishedWithProgressParser, MessageFromShellParser
import warnings


logger = logging.getLogger(__name__)


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

    def _send_line(self, line, **kwargs):
        warnings.warn("REMOVE BaseRemoteCommand._send_line()")
        return self.message_service.publish_message(line, **kwargs)

    def _process_line(self, cookie, subline):
        """Process a line of the spark-shell output."""

        # At this point, 'subline' was logged (ie: will appear
        #  on celery worker console or log file

        for parser in self.line_parsers:

            try:
                handled = parser.parse(subline)
                if handled:
                    return

            except Exception as e:
                logger.exception("Exception detected when handling")

                self.message_service.log_and_publish("Exception detected when "
                                                     "handling line: %s", e,
                                                     errorLine=True)

                # TODO: the previouws line must be logged as error

        #------------------------------------------------------------
        # It's a normal, plain line. Any parser handled the line
        #------------------------------------------------------------
        self._send_line(line=subline, lineIsFromRemoteOutput=True)
        return


class MkTemp(BaseRemoteCommand):

    def __init__(self, message_service, cookie):
        super(MkTemp, self).__init__(message_service, cookie)

    def mktemp(self):
        """Creates a temporary file on the remote server"""
        self.message_service.log_and_publish("Executing mktemp in "
                                             "remote server")
        ARGS = settings.SSH_BASE_ARGS + ["mktemp", "-t",
                                         "spark-job-script-XXXXXXXXXX",
                                         "--suffix=.scala"]
        self.message_service.log_and_publish("subprocess.Popen(%s)", ARGS)

        try:
            p = subprocess.Popen(ARGS, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except:
            self._send_line(line="_mktemp(): subprocess.Popen() failed")
            self._send_line(line="_mktemp():  + SSH_CMD: '{0}'".format(
                settings.SSH_BASE_ARGS))
            self._send_line(line="_mktemp():  + ARGS: '{0}'".format(ARGS))
            raise(Exception("_mktemp(): subprocess.Popen() failed"))

        try:
            stdout_data, stderr_data = p.communicate()
        except:
            self._send_line(line="_mktemp(): p.communicate() failed")
            raise(Exception("_mktemp(): p.communicate() failed"))

        if p.returncode != 0:
            self._send_line(line="ERROR: mktemp failed! "
                            "Exit status: {0}".format(p.returncode))
            self._send_line(line="===== STDOUT =====")
            for line in stdout_data.splitlines():
                self._send_line(line=line)
            self._send_line(line="===== STDERR =====")
            for line in stderr_data.splitlines():
                self._send_line(line=line)

            logger.error("_mktemp(): exit status != 0.")
            logger.error("_mktemp(): exit status: %s", p.returncode)
            logger.error("_mktemp(): STDOUT: %s", stdout_data)
            logger.error("_mktemp(): STDERR: %s", stderr_data)

            raise(Exception("_mktemp(): exit status != 0"))

        temp_file = stdout_data.splitlines()[0].strip()
        if not len(temp_file):
            self._send_line(line="ERROR: mktemp:  failed! "
                       "Temporary filename is empty")
            raise(Exception("Temporary filename is empty"))

        self.message_service.log_and_publish("Temporary file: %s", temp_file)
        # elf._send_line(
        #    line="Temporary file on server: {0}".format(temp_file))
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
        self.message_service.log_and_publish("subprocess.Popen(%s)", ARGS)

        try:
            p = subprocess.Popen(ARGS, stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            self._send_line(line="_send_script(): subprocess.Popen() failed")
            self._send_line(line="_send_script():  + SSH_CMD: '{0}'".format(
                settings.SSH_BASE_ARGS))
            self._send_line(line="_send_script():  + ARGS: '{0}'".format(ARGS))
            raise(Exception("_send_script(): subprocess.Popen() failed"))

        try:
            stdout_data, stderr_data = p.communicate(input=script)
        except:
            self._send_line(line="_send_script(): p.communicate() failed")
            raise(Exception("_send_script(): p.communicate() failed"))

        if p.returncode != 0:
            self._send_line(line="ERROR: couldn't send script! "
                       "Exit status: {0}".format(p.returncode))
            self._send_line(line="===== STDOUT =====")
            for line in stdout_data.splitlines():
                self._send_line(line=line)
            self._send_line(line="===== STDERR =====")
            for line in stderr_data.splitlines():
                self._send_line(line=line)

            logger.error("_send_script(): exit status != 0.")
            logger.error("_send_script(): exit status: %s", p.returncode)
            logger.error("_send_script(): STDOUT: %s", stdout_data)
            logger.error("_send_script(): STDERR: %s", stderr_data)

            raise(Exception("_send_script(): exit status != 0"))

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
        self.message_service.log_and_publish("subprocess.Popen(%s)", ARGS)

        try:
            p = subprocess.Popen(ARGS, stdout=subprocess.PIPE)
        except:
            self._send_line(line="_remote_spark_shell(): "
                            "subprocess.Popen() failed")
            self._send_line(line="_remote_spark_shell(): "
                            " + SSH_BASE_ARGS: '{0}'"
                            "".format(settings.SSH_BASE_ARGS))
            self._send_line(line="_remote_spark_shell(): "
                            " + ARGS: '{0}'".format(ARGS))
            raise(Exception("_remote_spark_shell(): "
                            "subprocess.Popen() failed"))

        first_line = True
        while True:
            line = p.stdout.readline()
            for subline in [sl.rstrip()
                            for sl in line.splitlines() if sl.strip()]:

                logger.info("spark-shell> %s", subline)

                if first_line:
                    first_line = False
                    self.message_service.log_and_publish("The first line of "
                                                         "spark shell "
                                                         "was received",
                                                         sparkStarted=True)

                self._process_line(self.cookie, subline)

            if not line:
                # this works because empty lines are '\n' and so
                # dont resovle to False
                break

        self.message_service.log_and_publish("Waiting for the child "
                                             "to join...")
        p.wait()

        self.message_service.log_and_publish("spark-shell job ended. "
                                             "exit_status: %s",
                                             p.returncode, jobFinishedOk=True,
                                             exitStatus=p.returncode)

        return p.returncode


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
        self.message_service.log_and_publish("subprocess.Popen(%s)", ARGS)

        try:
            p = subprocess.Popen(ARGS, stdout=subprocess.PIPE)
        except:
            self._send_line(line="_remote_cat(): "
                            "subprocess.Popen() failed")
            self._send_line(line="_remote_cat(): "
                            " + SSH_BASE_ARGS: '{0}'"
                            "".format(settings.SSH_BASE_ARGS))
            self._send_line(line="_remote_cat(): "
                            " + ARGS: '{0}'".format(ARGS))
            raise(Exception("_remote_cat(): "
                            "subprocess.Popen() failed"))

        first_line = True
        while True:
            line = p.stdout.readline()
            for subline in [sl.rstrip()
                            for sl in line.splitlines() if sl.strip()]:

                logger.info("remote_cat> %s", subline)

                if first_line:
                    first_line = False
                    self.message_service.log_and_publish("The first line of "
                                                         "spark shell "
                                                         "was received",
                                                         sparkStarted=True)

                self._process_line('', subline)

            if not line:
                # this works because empty lines are '\n' and so
                # dont resovle to False
                break

        self.message_service.log_and_publish("Waiting for the child "
                                             "to join...")
        p.wait()

        self.message_service.log_and_publish("cat finished. exit_status: %s",
                                             p.returncode, jobFinishedOk=True,
                                             exitStatus=p.returncode)

        return p.returncode


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
        self.message_service.log_and_publish("subprocess.Popen(%s)", ARGS)

        try:
            p = subprocess.Popen(ARGS, stdout=subprocess.PIPE)
        except:
            self._send_line(line="_remote_echo(): "
                            "subprocess.Popen() failed")
            self._send_line(line="_remote_echo(): "
                            " + SSH_BASE_ARGS: '{0}'"
                            "".format(settings.SSH_BASE_ARGS))
            self._send_line(line="_remote_echo(): "
                            " + ARGS: '{0}'".format(ARGS))
            raise(Exception("_remote_echo(): "
                            "subprocess.Popen() failed"))

        first_line = True
        while True:
            line = p.stdout.readline()
            for subline in [sl.rstrip()
                            for sl in line.splitlines() if sl.strip()]:

                logger.info("remote_echo> %s", subline)

                if first_line:
                    first_line = False
                    # self.message_service.log_and_publish("The first line of "
                    #                         "spark shell was received",
                    #                         sparkStarted=True)
                    self.message_service.log_and_publish("The first line of "
                                                         "'echo' was received")

                self._process_line('', subline)

            if not line:
                # this works because empty lines are '\n' and so
                # dont resovle to False
                break

        self.message_service.log_and_publish("Waiting for the child "
                                             "to join...")
        p.wait()

        self.message_service.log_and_publish("echo finished. exit_status: %s",
                                             p.returncode, jobFinishedOk=True,
                                             exitStatus=p.returncode)

        return p.returncode
