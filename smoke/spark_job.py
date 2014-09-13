# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import re
import subprocess
import uuid
from xml.dom.minidom import parseString

from django.conf import settings
from django.utils import timezone
from smoke.models import Job
from smoke.services.messages import MessageService


logger = logging.getLogger(__name__)

SSH_BASE_ARGS = settings.SSH_BASE_ARGS

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


def _test_regexes():
    test_line = "17:13:44 INFO scheduler.TaskSetManager: Finished TID " + \
        "9 in 11050 ms on hadoop3-touro1tb.hadoop.dev.docker." + \
        "data-tsunami.com (progress: 10/10)"
    match = RE_TASK_FINISHED_WITH_PROGRESS.search(test_line)
    assert match, "RE_TASK_FINISHED_WITH_PROGRESS FALLO"
    tid_id = match.group(1)
    took = match.group(2)
    host = match.group(3)
    progress_done = match.group(4)
    progress_total = match.group(5)

    int(tid_id)
    int(took)
    int(progress_done)
    int(progress_total)


class SparkService(object):
    """Service to launch and handle the execution of Spark Shell"""

    def __init__(self, *args, **kwargs):
        super(SparkService, self).__init__(*args, **kwargs)
        self.message_service = MessageService()

    def _send_line(self, line, **kwargs):
        # FIMXE: remove or rename this!
        return self.message_service.publish_message(line, **kwargs)

    def _log_and_publish(self, message, *args, **kwargs):
        return self.message_service.log_and_publish(message, *args, **kwargs)

    def _mktemp(self):
        """Creates a temporary file on the remote server"""
        self._log_and_publish("Executing mktemp in remote server")
        ARGS = SSH_BASE_ARGS + ["mktemp", "-t", "spark-job-script-XXXXXXXXXX",
                "--suffix=.scala"]
        self._log_and_publish("subprocess.Popen(%s)", ARGS)

        try:
            p = subprocess.Popen(ARGS, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except:
            self._send_line(line="_mktemp(): subprocess.Popen() failed")
            self._send_line(line="_mktemp():  + SSH_CMD: '{0}'".format(
                SSH_BASE_ARGS))
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

        self._log_and_publish("Temporary file: %s", temp_file)
        #elf._send_line(line="Temporary file on server: {0}".format(temp_file))
        return temp_file

    def _fix_script(self, script):
        """Agrega 'exit' al final, por las dudas..."""
        return script + "\n/* EXIT */\nexit\n"

    def _send_script(self, script):
        """Sube script a servidor.

        :returns: Path al archivo donde fue subido el script
        """
        self._log_and_publish("Sending script to server")

        temp_file = self._mktemp()

        ARGS = SSH_BASE_ARGS + ["cat > {0}".format(temp_file)]
        self._log_and_publish("subprocess.Popen(%s)", ARGS)

        try:
            p = subprocess.Popen(ARGS, stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            self._send_line(line="_send_script(): subprocess.Popen() failed")
            self._send_line(line="_send_script():  + SSH_CMD: '{0}'".format(
                SSH_BASE_ARGS))
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

        self._log_and_publish("Script contents were sent successfully")

        return temp_file

    def _process_line(self, cookie, subline):
        """Process a line of the spark-shell output."""

        # At this point, 'subline' was logged (ie: will appear
        #  on celery worker console or log file

        #------------------------------------------------------------
        # RE_APPLICATION_MASTER_LAUNCHED
        #------------------------------------------------------------
        if RE_APPLICATION_MASTER_LAUNCHED.search(subline):
            self._log_and_publish(subline,
                                    lineIsFromRemoteOutput=True,
                                    appMasterLaunched=True)
            return

        #------------------------------------------------------------
        # RE_TASK_FINISHED_WITH_PROGRESS
        #------------------------------------------------------------
        progress_match = RE_TASK_FINISHED_WITH_PROGRESS.search(subline)
        if progress_match:
            # tid_id = progress_match.group(1)
            # took = progress_match.group(2)
            # host = progress_match.group(3)
            progress_done = progress_match.group(4)
            progress_total = progress_match.group(5)
            self._log_and_publish(subline,
                                    lineIsFromRemoteOutput=True,
                                    progressUpdate=True,
                                    progressDone=int(progress_done),
                                    progressTotal=int(progress_total))
            return

        #------------------------------------------------------------
        # RE_MESSAGE_FROM_SHELL
        #------------------------------------------------------------
        msg_from_shell = RE_MESSAGE_FROM_SHELL.search(subline)
        if msg_from_shell:
            maybe_xml = msg_from_shell.group(1)

            try:
                # FIXME: parseString() is insecure
                root = parseString(maybe_xml)

                cookie_from_xml = root.getElementsByTagName(
                    'msgFromShell')[0].attributes['cookie'].value

                # Check cookie
                if cookie_from_xml != cookie:
                    # BAD COOKIE!
                    self._log_and_publish(
                        "ERROR: cookies doesn't matches. "
                        "Cookie: %s - From XML: %s",
                        cookie,
                        cookie_from_xml,
                        lineIsFromRemoteOutput=True,
                        errorLine=True)
                    # TODO: the previouws line must be logged as error
                    return

                # Check <errorLine>
                try:
                    errors = root.getElementsByTagName('errorLine')
                    assert errors
                except:
                    pass
                else:
                    for elem in errors:
                        error_line = elem.firstChild.data.rstrip()
                        self._log_and_publish(
                            error_line,
                            lineIsFromRemoteOutput=True,
                            errorLine=True)
                    return

                # Check <outputFileName>
                try:
                    output_filename = root.getElementsByTagName(
                        'outputFileName')[0].firstChild.data.strip()
                except:
                    pass
                else:
                    self._log_and_publish(
                        subline,
                        lineIsFromRemoteOutput=True,
                        outputFilenameReported=output_filename)
                    return

                # UNKNOW <msgFromShell> TYPE
                self._log_and_publish("ERROR: unknown type of line "
                                          "from shell: %s",
                                          subline,
                                          errorLine=True)
                # TODO: the previouws line must be logged as error
                return

            except BaseException as e:
                logger.exception()

                self._log_and_publish("Exception detected when "
                                          "processing line "
                                          "from shell: %s",
                                          e,
                                          errorLine=True)
                # TODO: the previouws line must be logged as error
                return

        #------------------------------------------------------------
        # It's a normal, plain line
        #------------------------------------------------------------
        self._send_line(line=subline, lineIsFromRemoteOutput=True)
        return

    def _remote_spark_shell(self, script_path):
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

        cookie = uuid.uuid4().hex
        self._log_and_publish("Using cookie: %s", cookie)

        ARGS = SSH_BASE_ARGS + ["env", "DATATSUNAMI_COOKIE=" + cookie,
                                "sh", "-c", REMOTE_COMMAND]
        self._log_and_publish("subprocess.Popen(%s)", ARGS)

        try:
            p = subprocess.Popen(ARGS, stdout=subprocess.PIPE)
        except:
            self._send_line(line="_remote_spark_shell(): "
                            "subprocess.Popen() failed")
            self._send_line(line="_remote_spark_shell(): "
                            " + SSH_BASE_ARGS: '{0}'".format(SSH_BASE_ARGS))
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
                    self._log_and_publish("The first line of spark shell "
                                            "was received", sparkStarted=True)

                self._process_line(cookie, subline)

            if not line:
                # this works because empty lines are '\n' and so
                # dont resovle to False
                break

        self._log_and_publish("Waiting for the child to join...")
        p.wait()

        self._log_and_publish("spark-shell job ended. exit_status: %s",
                                p.returncode, jobFinishedOk=True,
                                exitStatus=p.returncode)

        return p.returncode

    def _remote_cat(self, script_path):
        """Does a 'cat' of the script on the server.

        :returns: exit status of subprocess
        """

        #
        # FIXME: this is a copy-n-paste of _remote_spark_shell()
        #

        logger.info("Executing 'cat' (on server) of %s", script_path)

        ARGS = SSH_BASE_ARGS + ["cat", script_path]
        self._log_and_publish("subprocess.Popen(%s)", ARGS)

        try:
            p = subprocess.Popen(ARGS, stdout=subprocess.PIPE)
        except:
            self._send_line(line="_remote_cat(): "
                            "subprocess.Popen() failed")
            self._send_line(line="_remote_cat(): "
                            " + SSH_BASE_ARGS: '{0}'".format(SSH_BASE_ARGS))
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
                    self._log_and_publish("The first line of spark shell "
                                            "was received", sparkStarted=True)

                self._process_line('', subline)

            if not line:
                # this works because empty lines are '\n' and so
                # dont resovle to False
                break

        self._log_and_publish("Waiting for the child to join...")
        p.wait()

        self._log_and_publish("cat finished. exit_status: %s",
                                p.returncode, jobFinishedOk=True,
                                exitStatus=p.returncode)

        return p.returncode

    def _remote_echo(self):
        """Does a 'echo pong' on the server.

        :returns: exit status of subprocess
        """

        #
        # FIXME: this is a copy-n-paste of _remote_spark_shell()
        #

        logger.info("Executing 'echo pong' (on server)")

        ARGS = SSH_BASE_ARGS + ["echo", "pong"]
        self._log_and_publish("subprocess.Popen(%s)", ARGS)

        try:
            p = subprocess.Popen(ARGS, stdout=subprocess.PIPE)
        except:
            self._send_line(line="_remote_echo(): "
                            "subprocess.Popen() failed")
            self._send_line(line="_remote_echo(): "
                            " + SSH_BASE_ARGS: '{0}'".format(SSH_BASE_ARGS))
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
                    # self._log_and_publish("The first line of spark shell "
                    #                         "was received",
                    #                         sparkStarted=True)
                    self._log_and_publish("The first line of 'echo' "
                                            "was received")

                self._process_line('', subline)

            if not line:
                # this works because empty lines are '\n' and so
                # dont resovle to False
                break

        self._log_and_publish("Waiting for the child to join...")
        p.wait()

        self._log_and_publish("echo finished. exit_status: %s",
                                p.returncode, jobFinishedOk=True,
                                exitStatus=p.returncode)

        return p.returncode

    def _log_script(self, script):
        """Splits the string in lines and log each one"""
        logger.info("#-------------------------------------------------------")
        for line in script.splitlines():
            logger.info("# %s", line)
        logger.info("#-------------------------------------------------------")

    def launc_job(self, script, action):
        """Launches a job in the remote server"""
        job = Job(script=script, start=timezone.now())
        try:
            assert action in ("spark-shell", "cat", "echo")
            self._send_line(line="", receivedByWorker=True)

            if action == 'echo':
                self._remote_echo()
            else:
                script = self._fix_script(script)
                self._log_script(script)
                script_path = self._send_script(script)

                self._log_and_publish("Will launch action %s job on remote",
                                        action)
                if action == 'spark-shell':
                    self._remote_spark_shell(script_path)
                elif action == 'cat':
                    self._remote_cat(script_path)
        except:
            logger.exception("Exception detected")
            try:
                self._send_line(line="Exception detected",
                                jobFinishedWithError=True)
            except:
                logger.warn("Cound't send 'jobFinishedWithError' message "
                            "to web tier")

        job.log = self.message_service.get_log()
        job.end = timezone.now()
        job.save()

        self._log_and_publish("Job saved: %s", job.id, savedJobId=job.id)

_test_regexes()
