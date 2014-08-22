# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models


class JobManager(models.Manager):

    def latests_in_reverse_chronological(self):
        """Returns latests jobs"""
        return self.all().order_by("-id")[0:40]


class Job(models.Model):
    """Saves the information of a finished Job"""
    title = models.CharField(max_length=80)
    script = models.TextField()
    log = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()

    objects = JobManager()

    def save(self, *args, **kwargs):
        if self.script and not self.title:
            lines = [line.strip()
                     for line in self.script.splitlines()
                     if line.strip()]
            self.title = lines[0]
        if len(self.title) > 80:
            self.title = self.title[0:80]
        super(Job, self).save(*args, **kwargs)

    def __unicode__(self):
        return "Job {0}: {1}".format(self.id, self.title)
