# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import uuid

from django.conf import settings
from django.utils import timezone
from smoke.models import Job
from smoke.services import remote
from smoke.services.messages import MessageService


logger = logging.getLogger(__name__)

SSH_BASE_ARGS = settings.SSH_BASE_ARGS


class SparkService(object):
    """Service to launch and handle the execution of Spark Shell"""

    def __init__(self, *args, **kwargs):
        super(SparkService, self).__init__(*args, **kwargs)

        self.message_service = MessageService()
        self.cookie = uuid.uuid4().hex

    def _log_script(self, script):
        """Log the script using logger.info()"""
        logger.info("#-------------------------------------------------------")
        for line in script.splitlines():
            logger.info("# %s", line)
        logger.info("#-------------------------------------------------------")

    def _fix_script(self, script):
        """Adds 'exit' at the end of the script"""
        return script + "\n/* EXIT */\nexit\n"

    def launc_job(self, script, action):
        """Launches a job in the remote server"""
        job = Job(script=script, start=timezone.now())
        try:
            assert action in ("spark-shell", "cat", "echo")
            self.message_service.publish_message(line="",
                                                 receivedByWorker=True)

            if action == 'echo':
                remote.Echo(self.message_service, self.cookie).remote_echo()
            else:
                script = self._fix_script(script)
                self._log_script(script)
                script_path = remote.SendScript(
                    self.message_service, self.cookie).send_script(script)

                self.message_service.log_and_publish("Will launch action "
                                                     "%s job on remote",
                                                     action)
                if action == 'spark-shell':
                    remote.RunSparkShell(
                        self.message_service, self.cookie).run_spark_shell(
                            script_path)
                elif action == 'cat':
                    remote.Cat(
                        self.message_service, self.cookie).run_cat(script_path)
        except:
            logger.exception("Exception detected")
            try:
                self.message_service.publish_message(line="Exception detected",
                                                     jobFinishedWithError=True)
            except:
                logger.warn("Cound't send 'jobFinishedWithError' message "
                            "to web tier")

        job.log = self.message_service.get_log()
        job.end = timezone.now()
        job.save()

        self.message_service.log_and_publish("Job saved: %s", job.id,
                                             savedJobId=job.id)
