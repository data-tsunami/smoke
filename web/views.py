# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from web import tasks
from web.models import Job


def index(request):
    context = {}
    job_id = request.GET.get('restore_job_id', None)
    if job_id:
        context['script'] = Job.objects.get(id=job_id).script
    return render(request, 'index.html', context)


def post_job(request):
    if request.method == 'POST':
        script = request.POST['script']
        action = request.POST['action']
        tasks.spark_job_async(script, action)
        return HttpResponse('ok')
    return HttpResponse('ERROR: only post permited')


class JobListView(ListView):
    template_name = "job_list.html"
    model = Job

    def get_queryset(self):
        return Job.objects.latests_in_reverse_chronological()


class JobDetailView(DetailView):
    template_name = "job_details.html"
    model = Job
