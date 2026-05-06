from django.urls import re_path

from .views import dashboard


urlpatterns = [
    re_path(r'^dashboard/$', dashboard, name="dashboard"),
]
