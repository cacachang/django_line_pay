from django.contrib import admin
from django.urls import path, include
from . import views

app_name = "payment"

urlpatterns = [
  path('request', views.request, name="request"),
  path('confirm', views.confirm, name="confirm"),
  path('success', views.success, name="success"),
  path('fail', views.fail, name="success"),
]