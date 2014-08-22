# -*- coding: utf-8 -*-

"""
Setup the /admin site.
"""

from django.contrib import admin
from web.models import Job


admin.site.register(Job)
