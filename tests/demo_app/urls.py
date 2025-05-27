from django.urls import path
from . import views

urlpatterns = [
    path("", views.test_endpoint, name="test_demo"),
    path("async/", views.test_endpoint_async, name="test_demo_async"),
]
