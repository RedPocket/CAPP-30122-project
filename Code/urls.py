from django.conf.urls import url
from django.contrib import admin
from .views import *

urlpatterns = [
    url(r'^major/$', choose_major, name="choose_major"),
    url(r'^majortaken/$', choose_majortaken, name='choose_majortaken'),
    url(r'^majortotake/$', choose_majortotake, name='choose_majortotake'),
    url(r'^minor/$', choose_minor, name="choose_minor"),
    url(r'^minortaken/$', choose_minortaken, name='choose_minortaken'),
    url(r'^minortotake/$', choose_minortotake, name='choose_minortotake'),
    url(r'^schedules/$', schedules, name='schedules')
    ]