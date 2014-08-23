# -*- coding: utf-8 -*-

"""
Setup the /admin site.
"""

from django.contrib import admin
from smoke.models import Job


admin.site.register(Job)
