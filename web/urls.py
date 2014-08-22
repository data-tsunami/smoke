from django.conf.urls import patterns, include, url
from django.contrib import admin
from web import views


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^post_job', views.post_job, name='post_job'),
    url(r'^job_list', views.JobListView.as_view(), name='job_list'),
    url(r'^job/(?P<pk>\d+)/', views.JobDetailView.as_view(),
        name='job_details'),
    url(r'^admin/', include(admin.site.urls)),
)
