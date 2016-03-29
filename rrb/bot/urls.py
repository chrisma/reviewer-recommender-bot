from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^pull_request$', views.pull_request, name='pull_request'),
]